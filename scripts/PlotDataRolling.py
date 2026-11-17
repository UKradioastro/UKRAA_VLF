#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to create the rolling 24-hour plots (VLF receiver output with NOAA
# GOES primary X-ray flux overlay) using the generic gnuplot template
# PlotRolling.gp.
#
# Intended to be run from cron every 5 minutes, offset 2 minutes after the
# data fetches (2-59/5).
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
# Plots are written to <data>/WWWupload/ :
#   VLFrolling<frequency_hz>.png  (one per station)
#   NOAAxraysRolling.png          (when no stations are configured)
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
import subprocess
import sys
from datetime import timedelta

from vlf_common import (load_aerials, load_paths, log_error, log_message,
                        utc_now)

SOURCE = 'PlotDataRolling.py'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(SCRIPT_DIR, 'PlotRolling.gp')
# gnuplot executable - override with VLF_GNUPLOT for testing
GNUPLOT = os.environ.get('VLF_GNUPLOT', 'gnuplot')
GNUPLOT_TIMEOUT = 120  # seconds

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def gp_path(path):
    """Path in a form gnuplot accepts on any platform."""
    return path.replace('\\', '/')


def xray_file(data_path, day):
    return os.path.join(data_path, 'NOAA_xray', f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def aerial_file(data_path, callsign, day):
    return os.path.join(data_path, 'Aerial', callsign, f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


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


def main():
    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    log_message(logfiles_path, SOURCE, 'Started rolling 24-hour plots')

    now = utc_now()
    start = now - timedelta(hours=24)
    days = [start.date()]
    if now.date() != start.date():
        days.append(now.date())

    www_path = os.path.join(data_path, 'WWWupload')
    os.makedirs(www_path, exist_ok=True)

    xray_files = [path for path in (xray_file(data_path, day)
                                    for day in days) if os.path.isfile(path)]

    stations = load_aerials()['stations']
    if not stations:
        log_message(logfiles_path, SOURCE,
                    'No aerials configured in aerials.ini - '
                    'plotting X-ray data only')

    created = 0
    for station in stations or [None]:
        assigns = [
            f"StartTime='{start:{TIME_FORMAT}}'",
            f"EndTime='{now:{TIME_FORMAT}}'",
            f"GraphSubtitle='Rolling 24 hours to {now:%H:%M} UTC "
            f"- updated every 5 minutes'",
        ]
        have_data = False

        if station:
            khz = station['frequency_hz'] / 1000
            output_name = f'VLFrolling{station["frequency_hz"]}.png'
            title = (f'{station["callsign"]} VLF ({khz:g} kHz) and '
                     f'NOAA GOES primary X-ray data')
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
                            f'No aerial data for {station["callsign"]} yet '
                            f'- plotting X-ray data only')
        else:
            output_name = 'NOAAxraysRolling.png'
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

    log_message(logfiles_path, SOURCE,
                f'Completed rolling 24-hour plots - {created} plot(s) created')
    return 0 if created else 1


if __name__ == '__main__':
    sys.exit(main())
