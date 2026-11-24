#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to extract candidate SID (Sudden Ionospheric Disturbance) events
# from the VLF receiver data, for the monthly report to the BAA Radio
# Astronomy Group (see ReportSIDMonth.py and config/baa-report.ini).
#
# Intended to be run from cron once a day shortly after midnight UTC
# (after the yesterday plots), when yesterday's data files are complete.
# A different day can be reprocessed with --date YYYY-MM-DD.
#
# For each station configured in config/aerials.ini the day's NOAA GOES
# X-ray flare events (written by GetDataNOAAxrayFlares.py) define the
# candidate windows - only flares beginning between sunrise and sunset
# and outside the transmitter's daily off-air window are considered.
# Within each window the SID start, peak and end are MEASURED FROM THE
# RECEIVER DATA (the NOAA times are context only, never substituted):
#
#   - the baseline level and noise are taken from the quiet period before
#     the flare begins
#   - the peak is the largest departure from the baseline (positive or
#     negative - inverted SIDs are detected too)
#   - the start/end are where the departure rises above / falls back
#     below half the detection threshold; an end that cannot be measured
#     (signal still disturbed at the window end, sunset, next flare) is
#     recorded as "?" with an unassigned importance of "-"
#   - the importance rating follows the duration-based SID scale
#     (1- < 19 min, 1 19-25, 1+ 26-32, 2 33-45, 2+ 46-85, 3 86-125,
#      3+ > 125 min)
#
# The detection thresholds can be tuned in the [detection] section of
# config/baa-report.ini (see install/baa-report.ini.example).
#
# Each detected event is appended to the monthly candidates file
#   <data>/SID_events/<CALLSIGN>/YYYY/YYYY-MM.csv
# as a "candidate" row holding the automatic estimates (est_* columns),
# for the observer to review - confirm or correct the times in the obs_*
# columns and set the status to "reviewed" (or "rejected"). Rows the
# observer has already reviewed or rejected are never touched when a day
# is reprocessed; candidate rows are updated in place (keyed by the date
# and NOAA flare begin time).
#
# A plot of each event (receiver trace, X-ray flux, flare markers and the
# estimated start/peak/end) is written for review alongside the plots and
# on the intranet page's server:
#   <plots>/<CALLSIGN>/events/YYYY/YYYY-MM/<frequency_hz>-YYYY-MM-DD-HHMM.png
#   <temp>/events/YYYY-MM/<CALLSIGN>-YYYY-MM-DD-HHMM.png
#     (browsable at http://<your-pi>/temp/events/)
#
# All times are UTC. Activity is logged to logfiles/logfile.log; failures
# are logged to logfiles/logerror.log.
#
# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

import argparse
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from statistics import median

from vlf_common import (TIME_FORMAT, load_aerials, load_paths, log_error,
                        log_message, off_air_window, read_sun_times, utc_now)
from vlf_plot import aerial_file, flare_file, gp_path, run_gnuplot, xray_file
from vlf_sid import (END_UNKNOWN, STATUS_CANDIDATE, candidates_file,
                     importance_from_minutes, load_baa_settings,
                     read_candidates, write_candidates)

SOURCE = 'ExtractSIDEvents.py'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(SCRIPT_DIR, 'PlotSIDEvent.gp')

SMOOTH_SAMPLES = 5        # moving-median width for the receiver trace
MIN_PRE_SAMPLES = 10      # samples needed to establish the baseline
SUSTAIN_SECONDS = 120     # recovery must hold this long to count as the end
MAD_TO_SIGMA = 1.4826     # median absolute deviation -> standard deviation


def parse_time(text):
    return datetime.strptime(text, TIME_FORMAT).replace(tzinfo=timezone.utc)


# ==========================================================================================
#
# Day data
#
# ==========================================================================================

def read_flares(data_path, day):
    """The day's flare events (format written by GetDataNOAAxrayFlares.py)
    as dicts with begin/max/end datetimes (None if not reported) and the
    reported class. Events without a begin time are skipped."""
    path = flare_file(data_path, day)
    if not os.path.isfile(path):
        return []
    flares = []
    with open(path) as flare_data:
        for line in flare_data:
            fields = line.strip().split(',')
            if len(fields) < 8 or not fields[0]:
                continue
            try:
                begin = parse_time(fields[0])
            except ValueError:
                continue
            flares.append({
                'begin': begin,
                'max': _optional_time(fields[3]),
                'end': _optional_time(fields[6]),
                'class': (fields[4] or fields[2]).strip().upper(),
            })
    return sorted(flares, key=lambda flare: flare['begin'])


def _optional_time(text):
    try:
        return parse_time(text)
    except ValueError:
        return None


def read_aerial(data_path, callsign, day):
    """The day's receiver samples as a sorted list of (datetime, voltage),
    skipping unreadable rows and nan values."""
    path = aerial_file(data_path, callsign, day)
    if not os.path.isfile(path):
        return []
    samples = []
    with open(path) as aerial_data:
        for line in aerial_data:
            fields = line.strip().split(',')
            if len(fields) < 2:
                continue
            try:
                when = parse_time(fields[0])
                value = float(fields[1])
            except ValueError:
                continue
            if math.isnan(value):
                continue
            samples.append((when, value))
    samples.sort(key=lambda sample: sample[0])
    return samples


# ==========================================================================================
#
# Event measurement
#
# ==========================================================================================

def smooth(samples):
    """Moving-median smoothing of (time, value) samples, resistant to
    single-sample spikes."""
    half = SMOOTH_SAMPLES // 2
    values = [value for _, value in samples]
    return [(when, median(values[max(0, index - half):index + half + 1]))
            for index, (when, _) in enumerate(samples)]


def measure_event(samples, begin, window_start, window_end, settings):
    """Measure a SID within the window around a flare beginning at begin.

    samples is the day's full (time, voltage) list. Returns None when no
    significant departure from the pre-flare baseline is found, otherwise
    {'start', 'peak', 'end' (datetime or None), 'baseline', 'departure',
     'inverted', 'notes' (list)}.
    """
    window = smooth([sample for sample in samples
                     if window_start <= sample[0] <= window_end])
    if len(window) < MIN_PRE_SAMPLES * 2:
        return None

    notes = []
    pre = [value for when, value in window if when <= begin]
    if len(pre) < MIN_PRE_SAMPLES:
        pre = [value for _, value in window[:MIN_PRE_SAMPLES]]
        notes.append('baseline estimated from start of window')
    baseline = median(pre)
    noise = MAD_TO_SIGMA * median(abs(value - baseline) for value in pre)
    threshold = max(settings['noise_multiplier'] * noise,
                    settings['min_departure_v'])

    # Peak: largest departure from the baseline after the flare begins
    post = [(index, when, value - baseline)
            for index, (when, value) in enumerate(window) if when >= begin]
    if not post:
        return None
    peak_index, peak_time, peak_departure = max(
        post, key=lambda entry: abs(entry[2]))
    if abs(peak_departure) < threshold:
        return None

    half = threshold / 2

    # Start: walk back from the peak to the last quiet sample
    start = window[0][0]
    start_found = False
    for index in range(peak_index, -1, -1):
        if abs(window[index][1] - baseline) <= half:
            start = window[min(index + 1, peak_index)][0]
            start_found = True
            break
    if not start_found:
        notes.append('onset before window - start uncertain')

    # End: walk forward from the peak to a sustained return to baseline
    end = None
    for index in range(peak_index, len(window)):
        when, value = window[index]
        if abs(value - baseline) > half:
            continue
        sustained_until = when + timedelta(seconds=SUSTAIN_SECONDS)
        if all(abs(later_value - baseline) <= threshold
               for later_when, later_value in window[index:]
               if later_when <= sustained_until):
            end = when
            break

    return {
        'start': start,
        'peak': peak_time,
        'end': end,
        'baseline': baseline,
        'departure': peak_departure,
        'inverted': peak_departure < 0,
        'notes': notes,
    }


# ==========================================================================================
#
# Event plot
#
# ==========================================================================================

def plot_event(paths, station, day, event, window_start, window_end,
               flare, logfiles_path):
    """Create the review plot for one event. Returns the archive path
    relative to the plots folder, or '' when plotting failed."""
    goes_class = flare['class']
    # Name the files by the NOAA flare begin time, which is stable when
    # a day is reprocessed (the measured times may shift slightly)
    stamp = f'{day:%Y-%m-%d}-{flare["begin"]:%H%M}'
    archive_relative = os.path.join(
        station['callsign'], 'events', f'{day:%Y}', f'{day:%Y-%m}',
        f'{station["frequency_hz"]}-{stamp}.png')
    archive_path = os.path.join(paths['plots'], archive_relative)
    temp_folder = os.path.join(paths['temp'], 'events', f'{day:%Y-%m}')
    temp_path = os.path.join(
        temp_folder, f'{station["callsign"]}-{stamp}.png')
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    os.makedirs(temp_folder, exist_ok=True)

    khz = station['frequency_hz'] / 1000
    end_text = (f'{event["end"]:%H:%M} UTC' if event['end']
                else 'not measured')
    subtitle = (f'{day:%A %d %B %Y} - flare class {goes_class or "?"} - '
                f'start {event["start"]:%H:%M}, peak {event["peak"]:%H:%M}, '
                f'end {end_text}')
    assigns = [
        f"OutputFile='{gp_path(temp_path)}'",
        f"ArchiveFile='{gp_path(archive_path)}'",
        f"GraphTitle='{station['callsign']} VLF ({khz:g} kHz) "
        f"candidate SID event'",
        f"GraphSubtitle='{subtitle}'",
        f"StartTime='{window_start:{TIME_FORMAT}}'",
        f"EndTime='{window_end:{TIME_FORMAT}}'",
        f"AerialFile='{gp_path(aerial_file(paths['data'], station['callsign'], day))}'",
        f"AerialTitle='{station['callsign']} VLF ({khz:g} kHz)'",
        f"EventStart='{event['start']:{TIME_FORMAT}}'",
        f"EventPeak='{event['peak']:{TIME_FORMAT}}'",
    ]
    if event['end']:
        assigns.append(f"EventEnd='{event['end']:{TIME_FORMAT}}'")
    xray_path = xray_file(paths['data'], day)
    if os.path.isfile(xray_path):
        assigns.append(f"XrayFile='{gp_path(xray_path)}'")
    flare_path = flare_file(paths['data'], day)
    if os.path.isfile(flare_path):
        assigns.append(f"FlareFile='{gp_path(flare_path)}'")

    if run_gnuplot(TEMPLATE, assigns, logfiles_path, SOURCE,
                   archive_relative):
        return archive_relative.replace('\\', '/')
    return ''


# ==========================================================================================
#
# Candidate rows
#
# ==========================================================================================

def candidate_row(day, flare, event, plot_relative):
    duration = None
    if event['end']:
        duration = (event['end'] - event['start']).total_seconds() / 60
    notes = list(event['notes'])
    if event['inverted']:
        notes.append('inverted SID')
    return {
        'date': f'{day:%Y-%m-%d}',
        'goes_begin': f'{flare["begin"]:%H:%M}',
        'goes_class': flare['class'],
        'est_start': f'{event["start"]:%H:%M}',
        'est_peak': f'{event["peak"]:%H:%M}',
        'est_end': f'{event["end"]:%H:%M}' if event['end'] else END_UNKNOWN,
        'est_importance': importance_from_minutes(duration),
        'obs_start': '',
        'obs_peak': '',
        'obs_end': '',
        'obs_importance': '',
        'status': STATUS_CANDIDATE,
        'notes': '; '.join(notes),
        'plot': plot_relative,
    }


def upsert_candidates(path, new_rows):
    """Merge the day's new candidate rows into the monthly file, keyed by
    (date, goes_begin). Rows already reviewed or rejected by the observer
    are never modified; candidate rows are refreshed but keep any obs_*
    values already entered. Returns (added, updated)."""
    existing = {(row['date'], row['goes_begin']): row
                for row in read_candidates(path)}
    added = updated = 0
    for row in new_rows:
        key = (row['date'], row['goes_begin'])
        current = existing.get(key)
        if current is None:
            existing[key] = row
            added += 1
            continue
        if current['status'] != STATUS_CANDIDATE:
            continue
        for name in ('obs_start', 'obs_peak', 'obs_end', 'obs_importance'):
            row[name] = current[name]
        if current != row:
            existing[key] = row
            updated += 1
    if added or updated:
        write_candidates(path, list(existing.values()))
    return added, updated


# ==========================================================================================
#
# Main
#
# ==========================================================================================

def in_daylight(when, sunrise, sunset):
    if sunrise is None or sunset is None:
        return True
    return sunrise <= when <= sunset


def main():
    parser = argparse.ArgumentParser(
        description='Extract candidate SID events for the BAA report')
    parser.add_argument('--date', metavar='YYYY-MM-DD',
                        help='day to process (default: yesterday)')
    arguments = parser.parse_args()

    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    if arguments.date:
        try:
            day = datetime.strptime(arguments.date, '%Y-%m-%d').date()
        except ValueError:
            print(f'Invalid --date "{arguments.date}" - expected YYYY-MM-DD')
            return 1
    else:
        day = utc_now().date() - timedelta(days=1)

    settings = load_baa_settings()
    log_message(logfiles_path, SOURCE,
                f'Started SID event extraction for {day:%Y-%m-%d}')

    stations = load_aerials()['stations']
    if not stations:
        log_message(logfiles_path, SOURCE,
                    'No aerials configured in aerials.ini - nothing to do')
        return 0

    flares = read_flares(data_path, day)
    if not flares:
        log_message(logfiles_path, SOURCE,
                    f'No NOAA flare events recorded for {day:%Y-%m-%d} - '
                    'no candidate windows (check the NOAA data if '
                    'unexpected)')
        return 0

    sunrise_text, sunset_text = read_sun_times(data_path, day)
    sunrise = _optional_time(sunrise_text or '')
    sunset = _optional_time(sunset_text or '')
    if sunrise is None or sunset is None:
        log_message(logfiles_path, SOURCE,
                    f'No sunrise/sunset data for {day:%Y-%m-%d} - '
                    'considering flares for the whole day')

    day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    detected = 0
    for station in stations:
        samples = read_aerial(data_path, station['callsign'], day)
        if not samples:
            log_message(logfiles_path, SOURCE,
                        f'No aerial data for {station["callsign"]} on '
                        f'{day:%Y-%m-%d} - station skipped')
            continue

        off_air = None
        window = off_air_window(station['off_air'], day)
        if window:
            off_air = (parse_time(window[0]), parse_time(window[1]))

        new_rows = []
        for flare in flares:
            begin = flare['begin']
            if not in_daylight(begin, sunrise, sunset):
                continue
            if off_air and off_air[0] <= begin <= off_air[1]:
                log_message(logfiles_path, SOURCE,
                            f'{station["callsign"]}: flare at '
                            f'{begin:%H:%M} ignored - transmitter off-air')
                continue

            window_start = max(
                begin - timedelta(minutes=settings['pre_minutes']),
                day_start)
            window_end = min(
                (flare['end'] or begin)
                + timedelta(minutes=settings['post_minutes']),
                day_end - timedelta(seconds=1))

            event = measure_event(samples, begin, window_start, window_end,
                                  settings)
            if event is None:
                log_message(logfiles_path, SOURCE,
                            f'{station["callsign"]}: no SID detected for '
                            f'the {flare["class"] or "?"} flare at '
                            f'{begin:%H:%M}')
                continue

            if off_air and window_start <= off_air[1] \
                    and off_air[0] <= window_end:
                event['notes'].append('window overlaps off-air period')
            if sunset and event['end'] is None and window_end >= sunset:
                event['notes'].append('event ran into sunset')

            plot_relative = plot_event(paths, station, day, event,
                                       window_start, window_end,
                                       flare, logfiles_path)
            new_rows.append(candidate_row(day, flare, event, plot_relative))
            detected += 1
            end_text = (f'{event["end"]:%H:%M}' if event['end']
                        else END_UNKNOWN)
            log_message(logfiles_path, SOURCE,
                        f'{station["callsign"]}: candidate SID for the '
                        f'{flare["class"] or "?"} flare at {begin:%H:%M} - '
                        f'start {event["start"]:%H:%M}, '
                        f'peak {event["peak"]:%H:%M}, end {end_text}')

        if new_rows:
            path = candidates_file(data_path, station['callsign'],
                                   f'{day:%Y-%m}')
            try:
                added, updated = upsert_candidates(path, new_rows)
            except OSError as error:
                log_error(logfiles_path, SOURCE,
                          f'Failed to update {path}: {error}')
                continue
            log_message(logfiles_path, SOURCE,
                        f'Added {added} and updated {updated} '
                        f'candidate SID events in {path}')

    log_message(logfiles_path, SOURCE,
                f'Completed SID event extraction for {day:%Y-%m-%d} - '
                f'{detected} candidate(s) detected')
    return 0


if __name__ == '__main__':
    sys.exit(main())
