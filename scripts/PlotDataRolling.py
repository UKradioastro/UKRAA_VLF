#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to create the rolling plots (VLF receiver output with NOAA
# GOES primary X-ray flux overlay) using the generic gnuplot template
# PlotRolling.gp.
#
# By default a rolling 24-hour plot is produced; --days 3 or --days 7
# produce the rolling 3-day / 7-day plots (NOAA GOES style), when enabled
# in config/plots.ini. plots.ini also controls which overlays (sun
# shading, X-ray flux, flare markers) appear on each plot type.
#
# Intended to be run from cron: the 24-hour plot every 5 minutes, offset
# 2 minutes after the data fetches (2-59/5); the 3-day and 7-day plots
# hourly.
#
# One plot is created per station configured in config/aerials.ini
# (a channel counts as configured when both callsign and frequency_hz are
# set). While no stations are configured, a single X-ray only plot is
# produced instead. Missing data files are tolerated - the plot simply
# omits that trace (e.g. X-ray only until the aerial capture service runs).
#
# Aerial data is expected at:
#   <data>/Aerial/<CALLSIGN>/YYYY/YYYY-MM/YYYY-MM-DD.csv
# with records: yyyy-mm-dd hh:mm:ss,voltage
#
# Plots are written to the temp folder (<home>/temp/ by default):
#   VLFrolling<frequency_hz>.png  (one per station; --days 3/7 write
#   VLF3day<frequency_hz>.png / VLF7day<frequency_hz>.png)
#   NOAAxraysRolling.png          (when no stations are configured;
#   NOAAxrays3day.png / NOAAxrays7day.png for --days 3/7)
#
# A plots.json manifest describing the available plots is also refreshed
# in the temp folder for the intranet web page (WWW/index.html).
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
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from vlf_common import (TIME_FORMAT, load_aerials, load_paths,
                        load_plot_options, log_error, log_message,
                        off_air_window, read_sun_times, utc_now,
                        write_plot_manifest)

SOURCE = 'PlotDataRolling.py'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(SCRIPT_DIR, 'PlotRolling.gp')
# gnuplot executable - override with VLF_GNUPLOT for testing
GNUPLOT = os.environ.get('VLF_GNUPLOT', 'gnuplot')
GNUPLOT_TIMEOUT = 120  # seconds

# Per-window presentation: output names, canvas size, x-axis tics/format
WINDOWS = {
    1: {'section': 'rolling', 'station_name': 'VLFrolling{hz}.png',
        'fallback_name': 'NOAAxraysRolling.png', 'label': '24 hours',
        'subtitle': 'Rolling 24 hours to {now:%H:%M} UTC '
                    '- updated every 5 minutes',
        'extra_assigns': ['CanvasWidth=960', 'CanvasHeight=540']},
    3: {'section': '3day', 'station_name': 'VLF3day{hz}.png',
        'fallback_name': 'NOAAxrays3day.png', 'label': '3 days',
        'subtitle': 'Rolling 3 days to {now:%H:%M} UTC {now:%d %b} '
                    '- updated hourly',
        'extra_assigns': ['CanvasWidth=960', 'CanvasHeight=540',
                          'TicSeconds=43200', 'XTicFormat="%d %b\\n%H:%M"',
                          'CompactNights=1']},
    7: {'section': '7day', 'station_name': 'VLF7day{hz}.png',
        'fallback_name': 'NOAAxrays7day.png', 'label': '7 days',
        'subtitle': 'Rolling 7 days to {now:%H:%M} UTC {now:%d %b} '
                    '- updated hourly',
        'extra_assigns': ['CanvasWidth=960', 'CanvasHeight=540',
                          'TicSeconds=86400', "XTicFormat='%d %b'",
                          'CompactNights=1']},
}


def gp_path(path):
    """Path in a form gnuplot accepts on any platform."""
    return path.replace('\\', '/')


def xray_file(data_path, day):
    return os.path.join(data_path, 'NOAA_xray', f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def aerial_file(data_path, callsign, day):
    return os.path.join(data_path, 'Aerial', callsign, f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def flare_file(data_path, day):
    return os.path.join(data_path, 'NOAA_xray_flares', f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def parse_time(text):
    return datetime.strptime(text, TIME_FORMAT).replace(tzinfo=timezone.utc)


def sun_events(data_path, days):
    """Sunrise/sunset datetimes for each day in the window.

    A day without sun data borrows the other day's times shifted to its own
    date (sun times drift by ~1 minute per day). Returns {day: (rise, set)}.
    """
    found = {}
    for day in days:
        sunrise, sunset = read_sun_times(data_path, day)
        if sunrise and sunset:
            try:
                found[day] = (parse_time(sunrise), parse_time(sunset))
            except ValueError:
                pass
    if not found:
        return {}
    source_day, source_times = next(iter(found.items()))
    complete = {}
    for day in days:
        if day in found:
            complete[day] = found[day]
        else:
            shift = day - source_day
            complete[day] = (source_times[0] + shift, source_times[1] + shift)
    return complete


def night_intervals(start, end, daylight):
    """Periods within [start, end] outside the given daylight intervals."""
    nights = []
    current = start
    for sunrise, sunset in sorted(daylight):
        if sunrise > current:
            nights.append((current, min(sunrise, end)))
        current = max(current, sunset)
        if current >= end:
            break
    if current < end:
        nights.append((current, end))
    return [(night_start, night_end) for night_start, night_end in nights
            if night_end > night_start]


def run_gnuplot(assigns, logfiles_path, output_name):
    """Run the gnuplot template with the given variable assignments."""
    try:
        result = subprocess.run(
            [GNUPLOT, '-e', '; '.join(assigns), TEMPLATE],
            capture_output=True, text=True, timeout=GNUPLOT_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as error:
        log_error(logfiles_path, SOURCE,
                  f'gnuplot failed for {output_name}: {error}')
        return False
    if result.returncode != 0:
        detail = ' '.join(result.stderr.split())[:300]
        log_error(logfiles_path, SOURCE,
                  f'gnuplot failed for {output_name}: {detail}')
        return False
    return True


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create the rolling VLF + X-ray plots.')
    parser.add_argument('--days', type=int, choices=sorted(WINDOWS),
                        default=1,
                        help='rolling window length in days (default 1; '
                             '3 and 7 must be enabled in plots.ini)')
    return parser.parse_args()


def main():
    args = parse_args()
    window = WINDOWS[args.days]

    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    options = load_plot_options()[window['section']]
    if not options['enabled']:
        log_message(logfiles_path, SOURCE,
                    f'Rolling {window["label"]} plots disabled in '
                    f'plots.ini - nothing to do')
        return 0

    log_message(logfiles_path, SOURCE,
                f'Started rolling {window["label"]} plots')

    now = utc_now()
    start = now - timedelta(days=args.days)
    days = [start.date() + timedelta(days=offset)
            for offset in range((now.date() - start.date()).days + 1)]

    www_path = paths['temp']
    os.makedirs(www_path, exist_ok=True)

    xray_files = []
    if options['xray']:
        xray_files = [path for path in (xray_file(data_path, day)
                                        for day in days)
                      if os.path.isfile(path)]
    flare_files = []
    if options['flares']:
        flare_files = [path for path in (flare_file(data_path, day)
                                         for day in days)
                       if os.path.isfile(path)]

    # Night shading and sunrise/sunset marks, clipped to the window
    common_assigns = list(window.get('extra_assigns', []))
    sun = sun_events(data_path, days) if options['sun'] else {}
    if sun:
        nights = night_intervals(start, now, list(sun.values()))
        if nights:
            common_assigns.append(f'NightCount={len(nights)}')
            for index, (night_start, night_end) in enumerate(nights, 1):
                common_assigns.append(
                    f"Night{index}Start='{night_start:{TIME_FORMAT}}'")
                common_assigns.append(
                    f"Night{index}End='{night_end:{TIME_FORMAT}}'")
        marks = []
        for day in sorted(sun):
            sunrise, sunset = sun[day]
            if start <= sunrise <= now:
                marks.append((sunrise, f'Sunrise {sunrise:%H:%M} UTC'))
            if start <= sunset <= now:
                marks.append((sunset, f'Sunset {sunset:%H:%M} UTC'))
        if marks:
            common_assigns.append(f'SunMarkCount={len(marks)}')
            for index, (when, label) in enumerate(marks, 1):
                common_assigns.append(
                    f"SunMark{index}Time='{when:{TIME_FORMAT}}'")
                common_assigns.append(f"SunMark{index}Label='{label}'")
    for index, path in enumerate(flare_files, 1):
        common_assigns.append(f"FlareFile{index}='{gp_path(path)}'")

    stations = load_aerials()['stations']
    if not stations:
        log_message(logfiles_path, SOURCE,
                    'No aerials configured in aerials.ini - '
                    'plotting X-ray data only')

    created = 0
    for station in stations or [None]:
        subtitle = window['subtitle'].format(now=now)
        assigns = [
            f"StartTime='{start:{TIME_FORMAT}}'",
            f"EndTime='{now:{TIME_FORMAT}}'",
            f"GraphSubtitle='{subtitle}'",
        ] + common_assigns
        have_data = False

        if station:
            khz = station['frequency_hz'] / 1000
            output_name = window['station_name'].format(
                hz=station['frequency_hz'])
            title = f'{station["callsign"]} VLF ({khz:g} kHz)'
            if options['xray']:
                title += ' and NOAA GOES primary X-ray data'
            found = [path for path in
                     (aerial_file(data_path, station['callsign'], day)
                      for day in days) if os.path.isfile(path)]
            for index, path in enumerate(found, 1):
                assigns.append(f"AerialFile{index}='{gp_path(path)}'")
            if found:
                have_data = True
                assigns.append(f"AerialTitle='{station['callsign']} "
                               f"VLF ({khz:g} kHz)'")
                # Off-air annotation only on the 24-hour plot, and only
                # when monitoring this station with data
                if station['off_air'] and args.days == 1:
                    windows = []
                    for day in days:
                        window_times = off_air_window(station['off_air'], day)
                        if window_times is None:
                            continue
                        window_start = parse_time(window_times[0])
                        window_end = parse_time(window_times[1])
                        if window_end > start and window_start < now:
                            windows.append(window_times)
                    if windows:
                        assigns.append(f'OffAirCount={len(windows)}')
                        for index, window_times in enumerate(windows, 1):
                            assigns.append(
                                f"OffAir{index}Start='{window_times[0]}'")
                            assigns.append(
                                f"OffAir{index}End='{window_times[1]}'")
                            assigns.append(
                                f"OffAir{index}Mid='{window_times[2]}'")
                        assigns.append(f"OffAirLabel='{station['callsign']} "
                                       f"off-air {station['off_air']} UTC'")
            else:
                log_message(logfiles_path, SOURCE,
                            f'No aerial data for {station["callsign"]} yet '
                            f'- plotting X-ray data only')
        else:
            output_name = window['fallback_name']
            title = 'NOAA GOES primary X-ray data'

        for index, path in enumerate(xray_files, 1):
            assigns.append(f"XrayFile{index}='{gp_path(path)}'")
        if xray_files:
            have_data = True

        if not have_data:
            log_error(logfiles_path, SOURCE,
                      f'No data available for {output_name} - plot skipped')
            continue

        output_path = os.path.join(www_path, output_name)
        assigns.append(f"OutputFile='{gp_path(output_path)}'")
        assigns.append(f"GraphTitle='{title}'")

        if run_gnuplot(assigns, logfiles_path, output_name):
            created += 1
            log_message(logfiles_path, SOURCE, f'Created {output_path}')

    try:
        write_plot_manifest(www_path, stations)
    except OSError as error:
        log_error(logfiles_path, SOURCE,
                  f'Failed to write plots.json manifest: {error}')

    log_message(logfiles_path, SOURCE,
                f'Completed rolling {window["label"]} plots - '
                f'{created} plot(s) created')
    return 0 if created else 1


if __name__ == '__main__':
    sys.exit(main())
