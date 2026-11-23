#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Shared helpers for the plot scripts (PlotDataRolling.py, PlotDataPeriod.py
# and PlotDataYesterday.py):
#
#   - locating the per-day data files (aerial, X-ray, flares)
#   - sunrise/sunset lookup and night-interval calculation for a window
#   - building the common gnuplot variable assignments for a multi-day
#     window (night shading, sunrise/sunset marks, flare markers)
#   - running gnuplot with a template and variable assignments
#
# All times are UTC.
#
# ==========================================================================================

import os
import subprocess
from datetime import datetime, timezone

from vlf_common import TIME_FORMAT, log_error, read_sun_times

# gnuplot executable - override with VLF_GNUPLOT for testing
GNUPLOT = os.environ.get('VLF_GNUPLOT', 'gnuplot')
GNUPLOT_TIMEOUT = 120  # seconds


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


def window_overlays(data_path, options, start, end, days):
    """Data files and common gnuplot assignments for a multi-day window.

    Returns (xray_files, flare_files, assigns) where assigns holds the
    night shading, sunrise/sunset marks and flare-file variables enabled
    in options, clipped to [start, end].
    """
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

    assigns = []
    sun = sun_events(data_path, days) if options['sun'] else {}
    if sun:
        nights = night_intervals(start, end, list(sun.values()))
        if nights:
            assigns.append(f'NightCount={len(nights)}')
            for index, (night_start, night_end) in enumerate(nights, 1):
                assigns.append(
                    f"Night{index}Start='{night_start:{TIME_FORMAT}}'")
                assigns.append(
                    f"Night{index}End='{night_end:{TIME_FORMAT}}'")
        marks = []
        for day in sorted(sun):
            sunrise, sunset = sun[day]
            if start <= sunrise <= end:
                marks.append((sunrise, f'Sunrise {sunrise:%H:%M} UTC'))
            if start <= sunset <= end:
                marks.append((sunset, f'Sunset {sunset:%H:%M} UTC'))
        if marks:
            assigns.append(f'SunMarkCount={len(marks)}')
            for index, (when, label) in enumerate(marks, 1):
                assigns.append(f"SunMark{index}Time='{when:{TIME_FORMAT}}'")
                assigns.append(f"SunMark{index}Label='{label}'")
    for index, path in enumerate(flare_files, 1):
        assigns.append(f"FlareFile{index}='{gp_path(path)}'")

    return xray_files, flare_files, assigns


def run_gnuplot(template, assigns, logfiles_path, source, output_name):
    """Run a gnuplot template with the given variable assignments."""
    try:
        result = subprocess.run(
            [GNUPLOT, '-e', '; '.join(assigns), template],
            capture_output=True, text=True, timeout=GNUPLOT_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as error:
        log_error(logfiles_path, source,
                  f'gnuplot failed for {output_name}: {error}')
        return False
    if result.returncode != 0:
        detail = ' '.join(result.stderr.split())[:300]
        log_error(logfiles_path, source,
                  f'gnuplot failed for {output_name}: {detail}')
        return False
    return True
