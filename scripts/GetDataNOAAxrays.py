#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to get the GOES primary X-ray flux data from NOAA SWPC.
#
# Intended to be run from cron every 5 minutes. Each run:
#
#   1. Finds the newest record already stored (today's file, else yesterday's).
#   2. Fetches the 1-day JSON file:
#        https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json
#      If no data is stored yet, or the newest stored record is more than
#      20 hours old (long outage), the 3-day file is fetched instead to
#      backfill as much as possible:
#        https://services.swpc.noaa.gov/json/goes/primary/xrays-3-day.json
#   3. Pairs the two energy bands (0.05-0.4nm and 0.1-0.8nm) per minute and
#      appends only records not already stored, each to the daily file
#      matching its own timestamp (so day rollover is automatic):
#        <data>/NOAA_xray/YYYY/YYYY-MM/YYYY-MM-DD.csv
#      Folders are created as needed when the date changes.
#
# Data file record format:
#   yyyy-mm-dd hh:mm:ss,satellite,flux_short,0.05-0.4nm,flux_long,0.1-0.8nm
#
# All timestamps (data, log entries) are UTC.
#
# Activity is logged to logfiles/logfile.log; failures (NOAA service down,
# bad response, etc.) are logged to logfiles/logerror.log.
#
# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

import os
import sys
from datetime import datetime, timedelta, timezone

from vlf_common import fetch_json, load_paths, log_error, log_message, utc_now

SOURCE = 'GetDataNOAAxrays.py'

URL_1DAY = 'https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json'
URL_3DAY = 'https://services.swpc.noaa.gov/json/goes/primary/xrays-3-day.json'

# If the newest stored record is older than this, backfill from the 3-day file
BACKFILL_AGE = timedelta(hours=20)

ENERGY_SHORT = '0.05-0.4nm'
ENERGY_LONG = '0.1-0.8nm'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
NOAA_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


# ==========================================================================================
#
# Data file helpers
#
# ==========================================================================================

def day_file_path(data_path, day):
    """Path of the daily data file: <data>/NOAA_xray/YYYY/YYYY-MM/YYYY-MM-DD.csv"""
    return os.path.join(data_path, 'NOAA_xray', f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def last_timestamp_in_file(path):
    """Timestamp of the last record in a daily file, or None."""
    if not os.path.isfile(path):
        return None
    last_line = None
    with open(path) as data_file:
        for line in data_file:
            line = line.strip()
            if line:
                last_line = line
    if not last_line:
        return None
    try:
        when = datetime.strptime(last_line.split(',', 1)[0], TIME_FORMAT)
    except ValueError:
        return None
    return when.replace(tzinfo=timezone.utc)


def latest_stored_time(data_path):
    """Newest stored record time, checking today's then yesterday's file."""
    today = utc_now().date()
    for day in (today, today - timedelta(days=1)):
        when = last_timestamp_in_file(day_file_path(data_path, day))
        if when is not None:
            return when
    return None


def existing_timestamps(path):
    """Set of timestamp strings already stored in a daily file."""
    stamps = set()
    if os.path.isfile(path):
        with open(path) as data_file:
            for line in data_file:
                line = line.strip()
                if line:
                    stamps.add(line.split(',', 1)[0])
    return stamps


# ==========================================================================================
#
# NOAA parse
#
# ==========================================================================================

def pair_records(raw_data):
    """Pair the two energy bands per minute.

    Returns (records, incomplete_count) where each record is a tuple
    (datetime, satellite, flux_short, flux_long) sorted by time. Records
    missing either energy band (or with a null flux) are counted and skipped.
    """
    pairs = {}
    for item in raw_data:
        if not isinstance(item, dict):
            continue
        time_tag = item.get('time_tag')
        flux = item.get('flux')
        if not time_tag or flux is None:
            continue
        try:
            when = datetime.strptime(time_tag, NOAA_TIME_FORMAT)
            flux = float(flux)
        except (TypeError, ValueError):
            continue
        when = when.replace(tzinfo=timezone.utc)
        entry = pairs.setdefault(when, {'satellite': item.get('satellite', '')})
        if item.get('energy') == ENERGY_SHORT:
            entry['short'] = flux
        elif item.get('energy') == ENERGY_LONG:
            entry['long'] = flux

    records = []
    incomplete = 0
    for when in sorted(pairs):
        entry = pairs[when]
        if 'short' in entry and 'long' in entry:
            records.append((when, entry['satellite'],
                            entry['short'], entry['long']))
        else:
            incomplete += 1
    return records, incomplete


# ==========================================================================================
#
# Write data to daily files
#
# ==========================================================================================

def format_row(when, satellite, flux_short, flux_long):
    return (f'{when:{TIME_FORMAT}},{satellite},'
            f'{flux_short:.4e},{ENERGY_SHORT},'
            f'{flux_long:.4e},{ENERGY_LONG}')


def append_records(data_path, records):
    """Append records not already stored, each to its own day's file.

    Creates year/month folders as needed. Returns {file_path: count} of
    records appended.
    """
    by_day = {}
    for record in records:
        by_day.setdefault(record[0].date(), []).append(record)

    appended = {}
    for day in sorted(by_day):
        path = day_file_path(data_path, day)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        stored = existing_timestamps(path)
        new_records = [record for record in by_day[day]
                       if f'{record[0]:{TIME_FORMAT}}' not in stored]
        if not new_records:
            continue
        with open(path, 'a') as data_file:
            for record in new_records:
                data_file.write(format_row(*record) + '\n')
        appended[path] = len(new_records)
    return appended


# ==========================================================================================
#
# Main
#
# ==========================================================================================

def main():
    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    log_message(logfiles_path, SOURCE,
                'Started GOES primary X-ray data collection')

    # Decide which NOAA file to fetch
    url = URL_1DAY
    latest = latest_stored_time(data_path)
    if latest is None:
        url = URL_3DAY
        log_message(logfiles_path, SOURCE,
                    'No stored data found - fetching 3-day file to backfill')
    elif utc_now() - latest > BACKFILL_AGE:
        url = URL_3DAY
        log_message(logfiles_path, SOURCE,
                    f'Newest stored record ({latest:{TIME_FORMAT}} UTC) is '
                    'stale - fetching 3-day file to backfill')

    # Fetch from NOAA, with safeguards if the service is down
    try:
        raw_data = fetch_json(url, logfiles_path, SOURCE)
    except RuntimeError as error:
        log_error(logfiles_path, SOURCE, str(error))
        log_message(logfiles_path, SOURCE,
                    'Abandoned GOES primary X-ray data collection - '
                    'NOAA service unavailable (see logerror.log)')
        return 1

    if not isinstance(raw_data, list) or not raw_data:
        log_error(logfiles_path, SOURCE,
                  f'Unexpected or empty response from {url}')
        log_message(logfiles_path, SOURCE,
                    'Abandoned GOES primary X-ray data collection - '
                    'unusable response (see logerror.log)')
        return 1

    records, incomplete = pair_records(raw_data)
    if incomplete:
        log_message(logfiles_path, SOURCE,
                    f'Skipped {incomplete} records without both energy bands')
    if not records:
        log_error(logfiles_path, SOURCE,
                  f'No usable X-ray records in response from {url}')
        log_message(logfiles_path, SOURCE,
                    'Abandoned GOES primary X-ray data collection - '
                    'no usable records (see logerror.log)')
        return 1

    appended = append_records(data_path, records)
    if appended:
        for path, count in sorted(appended.items()):
            log_message(logfiles_path, SOURCE,
                        f'Appended {count} records to {path}')
    else:
        log_message(logfiles_path, SOURCE,
                    'No new records - data files already up to date')

    log_message(logfiles_path, SOURCE,
                'Completed GOES primary X-ray data collection')
    return 0


if __name__ == '__main__':
    sys.exit(main())
