#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to create the static (midnight-aligned) 3-day and 7-day plots
# (VLF receiver output with NOAA GOES primary X-ray flux overlay) using
# the generic gnuplot template PlotRolling.gp.
#
# Unlike the rolling plots, these cover complete UTC days: the window runs
# from midnight at the start of the period to last midnight. --days 3 or
# --days 7 select the period; each is produced when the matching 3day/7day
# section is enabled in config/plots.ini, which also controls the overlays
# (sun shading, X-ray flux, flare markers) - shared with the rolling
# 3-day/7-day plots.
#
# Intended to be run from cron once a day shortly after midnight UTC,
# after the yesterday plots.
#
# One plot is created per station configured in config/aerials.ini.
# While no stations are configured, a single X-ray only plot is produced
# instead. Missing data files are tolerated - the plot simply omits that
# trace.
#
# Plots are written to <temp>/periods/3day|7day/ (current, overwritten
# daily - the folder names the plot type, the filename is the station
# frequency in Hz) and a date-stamped copy (stamped with the last complete
# day of the period) to the plots archive:
#   <temp>/periods/3day/<frequency_hz>.png
#   <plots>/<CALLSIGN>/3day/YYYY/YYYY-MM/<frequency_hz>-YYYY-MM-DD.png
# or, while no stations are configured:
#   <temp>/periods/3day/NOAA.png
#   <plots>/NOAA/3day/YYYY/YYYY-MM/NOAA-YYYY-MM-DD.png
# (and likewise for 7day).
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
import shutil
import sys
from datetime import datetime, timedelta, timezone

from vlf_common import (TIME_FORMAT, load_aerials, load_paths,
                        load_plot_options, log_error, log_message,
                        plot_archive_path, utc_now, write_plot_manifest)
from vlf_plot import aerial_file, gp_path, run_gnuplot, window_overlays

SOURCE = 'PlotDataPeriod.py'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(SCRIPT_DIR, 'PlotRolling.gp')

# Per-period presentation: plots.ini section doubles as the folder name
WINDOWS = {
    3: {'section': '3day', 'label': '3 days',
        'subtitle': '3 days 00:00 {start:%d %b} to 00:00 {end:%d %b} UTC '
                    '- updated daily',
        'extra_assigns': ['CanvasWidth=960', 'CanvasHeight=540',
                          'TicSeconds=43200', 'XTicFormat="%d %b\\n%H:%M"',
                          'CompactNights=1']},
    7: {'section': '7day', 'label': '7 days',
        'subtitle': '7 days 00:00 {start:%d %b} to 00:00 {end:%d %b} UTC '
                    '- updated daily',
        'extra_assigns': ['CanvasWidth=960', 'CanvasHeight=540',
                          'TicSeconds=86400', "XTicFormat='%d %b'",
                          'CompactNights=1']},
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create the static (midnight-aligned) multi-day '
                    'VLF + X-ray plots.')
    parser.add_argument('--days', type=int, choices=sorted(WINDOWS),
                        default=3,
                        help='period length in complete days (default 3; '
                             'each must be enabled in plots.ini)')
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
                    f'{window["label"]} plots disabled in plots.ini '
                    f'- nothing to do')
        return 0

    log_message(logfiles_path, SOURCE,
                f'Started static {window["label"]} plots')

    # Complete UTC days: midnight <args.days> days ago to last midnight;
    # the archive copies are stamped with the last complete day
    end = datetime.combine(utc_now().date(), datetime.min.time(),
                           tzinfo=timezone.utc)
    start = end - timedelta(days=args.days)
    days = [start.date() + timedelta(days=offset)
            for offset in range(args.days)]
    last_day = days[-1]

    output_folder = os.path.join(paths['temp'], 'periods', window['section'])
    plots_path = paths['plots']
    os.makedirs(output_folder, exist_ok=True)

    # Night shading, sunrise/sunset marks and flare markers, clipped to
    # the window, plus the per-day data files that exist
    xray_files, _, overlay_assigns = window_overlays(
        data_path, options, start, end, days)
    common_assigns = list(window.get('extra_assigns', [])) + overlay_assigns

    stations = load_aerials()['stations']
    if not stations:
        log_message(logfiles_path, SOURCE,
                    'No aerials configured in aerials.ini - '
                    'plotting X-ray data only')

    created = 0
    for station in stations or [None]:
        subtitle = window['subtitle'].format(start=start, end=end)
        assigns = [
            f"StartTime='{start:{TIME_FORMAT}}'",
            f"EndTime='{end:{TIME_FORMAT}}'",
            f"GraphSubtitle='{subtitle}'",
        ] + common_assigns
        have_data = False

        if station:
            khz = station['frequency_hz'] / 1000
            output_name = f'{station["frequency_hz"]}.png'
            station_folder = station['callsign']
            stem = str(station['frequency_hz'])
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
            else:
                log_message(logfiles_path, SOURCE,
                            f'No aerial data for {station["callsign"]} in '
                            f'this period - plotting X-ray data only')
        else:
            output_name = 'NOAA.png'
            station_folder = 'NOAA'
            stem = 'NOAA'
            title = 'NOAA GOES primary X-ray data'

        for index, path in enumerate(xray_files, 1):
            assigns.append(f"XrayFile{index}='{gp_path(path)}'")
        if xray_files:
            have_data = True

        output_label = f'periods/{window["section"]}/{output_name}'
        if not have_data:
            log_error(logfiles_path, SOURCE,
                      f'No data available for {output_label} - plot skipped')
            continue

        output_path = os.path.join(output_folder, output_name)
        assigns.append(f"OutputFile='{gp_path(output_path)}'")
        assigns.append(f"GraphTitle='{title}'")

        if not run_gnuplot(TEMPLATE, assigns, logfiles_path, SOURCE,
                           output_label):
            continue

        archive_path = plot_archive_path(plots_path, station_folder,
                                         window['section'], last_day, stem)
        try:
            shutil.copyfile(output_path, archive_path)
        except OSError as error:
            log_error(logfiles_path, SOURCE,
                      f'Failed to archive {output_label} to '
                      f'{archive_path}: {error}')
            archive_path = None
        created += 1
        log_message(logfiles_path, SOURCE,
                    f'Created {output_path}'
                    + (f' and {archive_path}' if archive_path else ''))

    try:
        write_plot_manifest(paths['temp'], stations)
    except OSError as error:
        log_error(logfiles_path, SOURCE,
                  f'Failed to write plots.json manifest: {error}')

    log_message(logfiles_path, SOURCE,
                f'Completed static {window["label"]} plots - '
                f'{created} plot(s) created')
    return 0 if created else 1


if __name__ == '__main__':
    sys.exit(main())
