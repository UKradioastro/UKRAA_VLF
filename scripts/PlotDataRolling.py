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
# Plots are written to the rolling subfolders of the temp folder
# (<home>/temp/ by default), overwritten on each run - the folder names
# the plot type, the filename is the station frequency in Hz:
#   rolling/day/<frequency_hz>.png    (one per station; --days 3/7 write
#   rolling/3day/<frequency_hz>.png / rolling/7day/<frequency_hz>.png)
#   rolling/<type>/NOAA.png           (when no stations are configured)
# Rolling plots are snapshots and are not archived (the date-stamped
# archive under <plots>/ holds the midnight-aligned plots).
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
import sys
from datetime import timedelta

from vlf_common import (TIME_FORMAT, load_aerials, load_paths,
                        load_plot_options, log_error, log_message,
                        off_air_window, utc_now, write_plot_manifest)
from vlf_plot import (aerial_file, gp_path, parse_time, run_gnuplot,
                      window_overlays)

SOURCE = 'PlotDataRolling.py'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(SCRIPT_DIR, 'PlotRolling.gp')

# Per-window presentation: output folder, canvas size, x-axis tics/format
WINDOWS = {
    1: {'section': 'rolling', 'folder': 'day', 'label': '24 hours',
        'subtitle': 'Rolling 24 hours to {now:%H:%M} UTC '
                    '- updated every 5 minutes',
        'extra_assigns': ['CanvasWidth=960', 'CanvasHeight=540']},
    3: {'section': '3day', 'folder': '3day', 'label': '3 days',
        'subtitle': 'Rolling 3 days to {now:%H:%M} UTC {now:%d %b} '
                    '- updated hourly',
        'extra_assigns': ['CanvasWidth=960', 'CanvasHeight=540',
                          'TicSeconds=43200', 'XTicFormat="%d %b\\n%H:%M"',
                          'CompactNights=1']},
    7: {'section': '7day', 'folder': '7day', 'label': '7 days',
        'subtitle': 'Rolling 7 days to {now:%H:%M} UTC {now:%d %b} '
                    '- updated hourly',
        'extra_assigns': ['CanvasWidth=960', 'CanvasHeight=540',
                          'TicSeconds=86400', "XTicFormat='%d %b'",
                          'CompactNights=1']},
}


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

    output_folder = os.path.join(paths['temp'], 'rolling', window['folder'])
    os.makedirs(output_folder, exist_ok=True)

    # Night shading, sunrise/sunset marks and flare markers, clipped to
    # the window, plus the per-day data files that exist
    xray_files, _, overlay_assigns = window_overlays(
        data_path, options, start, now, days)
    common_assigns = list(window.get('extra_assigns', [])) + overlay_assigns

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
            output_name = f'{station["frequency_hz"]}.png'
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
            output_name = 'NOAA.png'
            title = 'NOAA GOES primary X-ray data'

        for index, path in enumerate(xray_files, 1):
            assigns.append(f"XrayFile{index}='{gp_path(path)}'")
        if xray_files:
            have_data = True

        output_label = f'rolling/{window["folder"]}/{output_name}'
        if not have_data:
            log_error(logfiles_path, SOURCE,
                      f'No data available for {output_label} - plot skipped')
            continue

        output_path = os.path.join(output_folder, output_name)
        assigns.append(f"OutputFile='{gp_path(output_path)}'")
        assigns.append(f"GraphTitle='{title}'")

        if run_gnuplot(TEMPLATE, assigns, logfiles_path, SOURCE,
                       output_label):
            created += 1
            log_message(logfiles_path, SOURCE, f'Created {output_path}')

    try:
        write_plot_manifest(paths['temp'], stations)
    except OSError as error:
        log_error(logfiles_path, SOURCE,
                  f'Failed to write plots.json manifest: {error}')

    log_message(logfiles_path, SOURCE,
                f'Completed rolling {window["label"]} plots - '
                f'{created} plot(s) created')
    return 0 if created else 1


if __name__ == '__main__':
    sys.exit(main())
