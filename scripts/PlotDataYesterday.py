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
# Plots are written to <data>/WWWupload/ (current, overwritten daily) and a
# date-stamped copy to <data>/Plots/ (archive):
#   VLFplot<frequency_hz>.png / VLFplot<frequency_hz>-YYYYMMDD.png
#   NOAAxraysYesterday.png    / NOAAxraysYesterday-YYYYMMDD.png
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
from datetime import datetime, timedelta

from vlf_common import (load_aerials, load_paths, log_error, log_message,
                        utc_now)

SOURCE = 'PlotDataYesterday.py'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(SCRIPT_DIR, 'PlotYesterday.gp')
# gnuplot executable - override with VLF_GNUPLOT for testing
GNUPLOT = os.environ.get('VLF_GNUPLOT', 'gnuplot')
GNUPLOT_TIMEOUT = 120  # seconds

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def gp_path(path):
    """Path in a form gnuplot accepts on any platform."""
    return path.replace('\\', '/')


def day_file(data_path, *parts, day):
    return os.path.join(data_path, *parts, f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def read_sun_times(data_path, day):
    """Sunrise and sunset timestamps from the daily sun file, or (None, None)."""
    path = day_file(data_path, 'Sun', day=day)
    if not os.path.isfile(path):
        return None, None
    with open(path) as sun_file:
        fields = sun_file.readline().strip().split(',')
    if len(fields) >= 4 and fields[1] == 'sunrise' and fields[3] == 'sunset':
        return fields[0], fields[2]
    return None, None


def off_air_window(text, day):
    """Parse an "HH:MM-HH:MM" off-air window into full timestamps plus the
    window midpoint (for label placement), or None."""
    try:
        start_text, end_text = (part.strip() for part in text.split('-'))
        start = datetime.strptime(start_text, '%H:%M')
        end = datetime.strptime(end_text, '%H:%M')
    except ValueError:
        return None
    mid = start + (end - start) / 2
    return (f'{day:%Y-%m-%d} {start_text}:00',
            f'{day:%Y-%m-%d} {end_text}:00',
            f'{day:%Y-%m-%d} {mid:%H:%M}:00')


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

    log_message(logfiles_path, SOURCE, "Started yesterday's plots")

    yesterday = utc_now().date() - timedelta(days=1)
    start = f'{yesterday:%Y-%m-%d} 00:00:00'
    end = f'{yesterday + timedelta(days=1):%Y-%m-%d} 00:00:00'

    www_path = os.path.join(data_path, 'WWWupload')
    plots_path = os.path.join(data_path, 'Plots')
    os.makedirs(www_path, exist_ok=True)
    os.makedirs(plots_path, exist_ok=True)

    xray_path = day_file(data_path, 'NOAA_xray', day=yesterday)
    flare_path = day_file(data_path, 'NOAA_xray_flares', day=yesterday)
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
        have_data = False

        if station:
            khz = station['frequency_hz'] / 1000
            base_name = f'VLFplot{station["frequency_hz"]}'
            title = (f'{station["callsign"]} VLF ({khz:g} kHz) and '
                     f'NOAA GOES primary X-ray data')
            aerial_path = day_file(data_path, 'Aerial', station['callsign'],
                                   day=yesterday)
            if os.path.isfile(aerial_path):
                have_data = True
                assigns.append(f"AerialFile='{gp_path(aerial_path)}'")
                assigns.append(f"AerialTitle='{station['callsign']} "
                               f"VLF ({khz:g} kHz)'")
                # Sun shading and off-air window only make sense on VLF plots
                if sunrise and sunset:
                    assigns.append(f"SunriseTime='{sunrise}'")
                    assigns.append(f"SunsetTime='{sunset}'")
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
            base_name = 'NOAAxraysYesterday'
            title = 'NOAA GOES primary X-ray data'

        if os.path.isfile(xray_path):
            have_data = True
            assigns.append(f"XrayFile='{gp_path(xray_path)}'")
        if os.path.isfile(flare_path):
            assigns.append(f"FlareFile='{gp_path(flare_path)}'")

        if not have_data:
            log_error(logfiles_path, SOURCE,
                      f'No data available for {base_name}.png - plot skipped')
            continue

        output_path = os.path.join(www_path, f'{base_name}.png')
        archive_path = os.path.join(plots_path,
                                    f'{base_name}-{yesterday:%Y%m%d}.png')
        assigns.append(f"OutputFile='{gp_path(output_path)}'")
        assigns.append(f"ArchiveFile='{gp_path(archive_path)}'")
        assigns.append(f"GraphTitle='{title}'")

        if run_gnuplot(assigns, logfiles_path, f'{base_name}.png'):
            created += 1
            log_message(logfiles_path, SOURCE,
                        f'Created {output_path} and {archive_path}')

    log_message(logfiles_path, SOURCE,
                f"Completed yesterday's plots - {created} plot(s) created")
    return 0 if created else 1


if __name__ == '__main__':
    sys.exit(main())
