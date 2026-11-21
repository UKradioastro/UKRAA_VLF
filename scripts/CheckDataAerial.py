#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Independent watchdog for the VLF aerial capture service (GetDataAerial.py).
#
# Intended to be run from cron every 10 minutes. For every channel
# configured in aerials.ini it checks the station's daily data files
# (<data>/Aerial/<CALLSIGN>/YYYY/YYYY-MM/YYYY-MM-DD.csv) and reports to
# logerror.log if:
#
#   1. No record is newer than STALE_MINUTES (data has stopped arriving -
#      service dead/disabled, disk full, clock problem, etc.), or
#   2. The newest NAN_WINDOW records are all "nan" (the service is running
#      but every ADC read is failing).
#
# Alert-only: recovery is handled by the systemd watchdog and the stalled-
# ADC self-restart inside GetDataAerial.py. Healthy runs log nothing, so
# logfile.log is not flooded.
#
# All timestamps (data, log entries) are UTC.
#
# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

import math
import os
import sys
from datetime import datetime, timedelta, timezone

from vlf_common import load_aerials, load_paths, log_error, utc_now

SOURCE = 'CheckDataAerial.py'

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
STALE_MINUTES = 2       # newest record older than this -> data has stalled
NAN_WINDOW = 30         # newest records all nan -> ADC read failures


def day_file_path(data_path, callsign, day):
    """Path of a station's daily file:
    <data>/Aerial/<CALLSIGN>/YYYY/YYYY-MM/YYYY-MM-DD.csv"""
    return os.path.join(data_path, 'Aerial', callsign, f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def recent_records(data_path, callsign, count):
    """Newest <count> (timestamp, value) tuples for a station, reading
    yesterday's then today's daily file. Unparseable lines are skipped."""
    today = utc_now().date()
    records = []
    for day in (today - timedelta(days=1), today):
        path = day_file_path(data_path, callsign, day)
        if not os.path.isfile(path):
            continue
        with open(path) as data_file:
            for line in data_file:
                fields = line.strip().split(',')
                if len(fields) < 2:
                    continue
                try:
                    when = datetime.strptime(fields[0], TIME_FORMAT)
                    value = float(fields[1])
                except ValueError:
                    continue
                records.append((when.replace(tzinfo=timezone.utc), value))
    return records[-count:]


def check_station(data_path, logfiles_path, station):
    """Alert to logerror.log if a station's data is stale or all-nan.
    Returns True if healthy."""
    callsign = station['callsign']
    records = recent_records(data_path, callsign, NAN_WINDOW)

    if not records:
        log_error(logfiles_path, SOURCE,
                  f'No aerial data found for {callsign} (channel '
                  f'{station["channel"]}) today or yesterday - is the '
                  f'ukraa-vlf-aerial service running?')
        return False

    newest = records[-1][0]
    age = utc_now() - newest
    if age > timedelta(minutes=STALE_MINUTES):
        log_error(logfiles_path, SOURCE,
                  f'Aerial data for {callsign} has stalled - newest record '
                  f'{newest:{TIME_FORMAT}} UTC is '
                  f'{int(age.total_seconds() // 60)} minutes old - is the '
                  f'ukraa-vlf-aerial service running?')
        return False

    if (len(records) >= NAN_WINDOW
            and all(math.isnan(value) for _, value in records)):
        log_error(logfiles_path, SOURCE,
                  f'Aerial data for {callsign} is all nan for the newest '
                  f'{NAN_WINDOW} records - ADC reads are failing (check '
                  f'the I2C bus, wiring and logerror.log entries from '
                  f'GetDataAerial.py)')
        return False

    return True


def main():
    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    stations = load_aerials()['stations']
    if not stations:
        return 0        # nothing configured - nothing to check

    healthy = all([check_station(data_path, logfiles_path, station)
                   for station in stations])
    return 0 if healthy else 1


if __name__ == '__main__':
    sys.exit(main())
