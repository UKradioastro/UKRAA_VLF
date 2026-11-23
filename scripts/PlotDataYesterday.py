#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to create yesterday's full-day plots (VLF receiver output with
# NOAA GOES primary X-ray flux, sunrise/sunset shading and solar flare
# events) using the generic gnuplot template PlotYesterday.gp.
#
# Intended to be run from cron once a day shortly after midnight UTC, when
# yesterday's data files are complete.
#
# One plot is created per station configured in config/aerials.ini
# (a channel counts as configured when both callsign and frequency_hz are
# set). While no stations are configured, a single X-ray only plot is
# produced instead. Missing data files are tolerated - the plot simply
# omits that trace.
#
# Plots are written to <temp>/periods/yesterday/ (current, overwritten
# daily - the folder names the plot type, the filename is the station
# frequency in Hz) and a date-stamped copy to the plots archive:
#   <temp>/periods/yesterday/<frequency_hz>.png
#   <plots>/<CALLSIGN>/day/YYYY/YYYY-MM/<frequency_hz>-YYYY-MM-DD.png
# or, while no stations are configured:
#   <temp>/periods/yesterday/NOAA.png
#   <plots>/NOAA/day/YYYY/YYYY-MM/NOAA-YYYY-MM-DD.png
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

import os
import sys
from datetime import timedelta

from vlf_common import (load_aerials, load_paths, load_plot_options,
                        log_error, log_message, off_air_window,
                        plot_archive_path, read_sun_times, utc_now,
                        write_plot_manifest)
from vlf_plot import gp_path, run_gnuplot

SOURCE = 'PlotDataYesterday.py'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(SCRIPT_DIR, 'PlotYesterday.gp')


def day_file(data_path, *parts, day):
    return os.path.join(data_path, *parts, f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def main():
    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    # Overlay options for the yesterday plots (config/plots.ini)
    options = load_plot_options()['yesterday']
    if not options['enabled']:
        log_message(logfiles_path, SOURCE,
                    "Yesterday's plots disabled in plots.ini - nothing to do")
        return 0

    log_message(logfiles_path, SOURCE, "Started yesterday's plots")

    yesterday = utc_now().date() - timedelta(days=1)
    start = f'{yesterday:%Y-%m-%d} 00:00:00'
    end = f'{yesterday + timedelta(days=1):%Y-%m-%d} 00:00:00'

    output_folder = os.path.join(paths['temp'], 'periods', 'yesterday')
    plots_path = paths['plots']
    os.makedirs(output_folder, exist_ok=True)

    xray_path = day_file(data_path, 'NOAA_xray', day=yesterday)
    flare_path = day_file(data_path, 'NOAA_xray_flares', day=yesterday)
    sunrise = sunset = None
    if options['sun']:
        sunrise, sunset = read_sun_times(data_path, yesterday)

    stations = load_aerials()['stations']
    if not stations:
        log_message(logfiles_path, SOURCE,
                    'No aerials configured in aerials.ini - '
                    'plotting X-ray data only')

    created = 0
    for station in stations or [None]:
        assigns = [
            f"StartTime='{start}'",
            f"EndTime='{end}'",
            f"GraphSubtitle='{yesterday:%A %d %B %Y} "
            f"- updated daily at 00:20 UTC'",
        ]
        # Sun shading shows when this station could have detected flares,
        # so include it even while only X-ray data is plotted
        if sunrise and sunset:
            assigns.append(f"SunriseTime='{sunrise}'")
            assigns.append(f"SunsetTime='{sunset}'")
        have_data = False

        if station:
            khz = station['frequency_hz'] / 1000
            output_name = f'{station["frequency_hz"]}.png'
            station_folder = station['callsign']
            stem = str(station['frequency_hz'])
            title = f'{station["callsign"]} VLF ({khz:g} kHz)'
            if options['xray']:
                title += ' and NOAA GOES primary X-ray data'
            aerial_path = day_file(data_path, 'Aerial', station['callsign'],
                                   day=yesterday)
            if os.path.isfile(aerial_path):
                have_data = True
                assigns.append(f"AerialFile='{gp_path(aerial_path)}'")
                assigns.append(f"AerialTitle='{station['callsign']} "
                               f"VLF ({khz:g} kHz)'")
                # Off-air annotation only when monitoring this station with data
                window = off_air_window(station['off_air'], yesterday)
                if window:
                    assigns.append(f"OffAirStart='{window[0]}'")
                    assigns.append(f"OffAirEnd='{window[1]}'")
                    assigns.append(f"OffAirMid='{window[2]}'")
                    assigns.append(f"OffAirLabel='{station['callsign']} "
                                   f"off-air {station['off_air']} UTC'")
            else:
                log_message(logfiles_path, SOURCE,
                            f'No aerial data for {station["callsign"]} on '
                            f'{yesterday:%Y-%m-%d} - plotting X-ray data only')
        else:
            output_name = 'NOAA.png'
            station_folder = 'NOAA'
            stem = 'NOAA'
            title = 'NOAA GOES primary X-ray data'

        if options['xray'] and os.path.isfile(xray_path):
            have_data = True
            assigns.append(f"XrayFile='{gp_path(xray_path)}'")
        if options['flares'] and os.path.isfile(flare_path):
            assigns.append(f"FlareFile='{gp_path(flare_path)}'")

        output_label = f'periods/yesterday/{output_name}'
        if not have_data:
            log_error(logfiles_path, SOURCE,
                      f'No data available for {output_label} - plot skipped')
            continue

        output_path = os.path.join(output_folder, output_name)
        archive_path = plot_archive_path(plots_path, station_folder, 'day',
                                         yesterday, stem)
        assigns.append(f"OutputFile='{gp_path(output_path)}'")
        assigns.append(f"ArchiveFile='{gp_path(archive_path)}'")
        assigns.append(f"GraphTitle='{title}'")

        if run_gnuplot(TEMPLATE, assigns, logfiles_path, SOURCE,
                       output_label):
            created += 1
            log_message(logfiles_path, SOURCE,
                        f'Created {output_path} and {archive_path}')

    try:
        write_plot_manifest(paths['temp'], stations)
    except OSError as error:
        log_error(logfiles_path, SOURCE,
                  f'Failed to write plots.json manifest: {error}')

    log_message(logfiles_path, SOURCE,
                f"Completed yesterday's plots - {created} plot(s) created")
    return 0 if created else 1


if __name__ == '__main__':
    sys.exit(main())
