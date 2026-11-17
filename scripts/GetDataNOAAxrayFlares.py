#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to get the GOES primary X-ray flare event data from NOAA SWPC.
#
# Intended to be run from cron every 5 minutes. Each run fetches the 7-day
# flare event file:
#   https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json
#
# Flare events UPDATE IN PLACE while in progress (begin is recorded first,
# then max, then end, and the classes are revised), so this script upserts:
# each event is keyed by its begin time and the stored row is replaced
# whenever NOAA revises the event. Using the 7-day file means any outage
# shorter than a week self-heals on the next successful run.
#
# Events are stored in daily files by the date of the event begin time:
#   <data>/NOAA_xray_flares/YYYY/YYYY-MM/YYYY-MM-DD.csv
# Folders are created as needed when the date changes.
#
# Data file record format (fields blank if not yet reported by NOAA):
#   begin yyyy-mm-dd hh:mm:ss,satellite,begin_class,
#   max yyyy-mm-dd hh:mm:ss,max_class,max_flux,
#   end yyyy-mm-dd hh:mm:ss,end_class
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
from datetime import datetime, timezone

from vlf_common import fetch_json, load_paths, log_error, log_message

SOURCE = 'GetDataNOAAxrayFlares.py'

URL_7DAY = ('https://services.swpc.noaa.gov/json/goes/primary/'
            'xray-flares-7-day.json')

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
NOAA_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


# ==========================================================================================
#
# Parse NOAA flare events
#
# ==========================================================================================

def parse_noaa_time(text):
    """NOAA time tag -> aware UTC datetime, or None if absent/invalid."""
    if not text:
        return None
    try:
        when = datetime.strptime(text, NOAA_TIME_FORMAT)
    except (TypeError, ValueError):
        return None
    return when.replace(tzinfo=timezone.utc)


def format_time(when):
    return f'{when:{TIME_FORMAT}}' if when else ''


def format_row(event):
    """CSV row for one flare event (see header comment for field order)."""
    begin = parse_noaa_time(event.get('begin_time'))
    max_time = parse_noaa_time(event.get('max_time'))
    end = parse_noaa_time(event.get('end_time'))
    max_flux = event.get('max_xrlong')
    return ','.join([
        format_time(begin),
        str(event.get('satellite', '')),
        event.get('begin_class') or '',
        format_time(max_time),
        event.get('max_class') or '',
        f'{max_flux:.4e}' if isinstance(max_flux, (int, float)) else '',
        format_time(end),
        event.get('end_class') or '',
    ])


def events_by_day(raw_data):
    """Group flare events by the date of their begin time.

    Returns ({date: {begin_timestamp_string: row}}, skipped_count).
    """
    days = {}
    skipped = 0
    for event in raw_data:
        if not isinstance(event, dict):
            skipped += 1
            continue
        begin = parse_noaa_time(event.get('begin_time'))
        if begin is None:
            skipped += 1
            continue
        day_rows = days.setdefault(begin.date(), {})
        day_rows[format_time(begin)] = format_row(event)
    return days, skipped


# ==========================================================================================
#
# Write data to daily files (upsert)
#
# ==========================================================================================

def day_file_path(data_path, day):
    """Path of the daily flare file: <data>/NOAA_xray_flares/YYYY/YYYY-MM/YYYY-MM-DD.csv"""
    return os.path.join(data_path, 'NOAA_xray_flares', f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def read_existing_rows(path):
    """Existing rows keyed by begin timestamp (first field)."""
    rows = {}
    if os.path.isfile(path):
        with open(path) as data_file:
            for line in data_file:
                line = line.strip()
                if line:
                    rows[line.split(',', 1)[0]] = line
    return rows


def upsert_events(data_path, days):
    """Merge fetched events into the daily files, rewriting a file only
    when an event is new or has been revised by NOAA.

    Returns {file_path: (added, updated)}.
    """
    changed = {}
    for day in sorted(days):
        path = day_file_path(data_path, day)
        existing = read_existing_rows(path)
        added = updated = 0
        for begin, row in days[day].items():
            if begin not in existing:
                added += 1
            elif existing[begin] != row:
                updated += 1
            else:
                continue
            existing[begin] = row
        if not (added or updated):
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as data_file:
            for begin in sorted(existing):
                data_file.write(existing[begin] + '\n')
        changed[path] = (added, updated)
    return changed


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
                'Started GOES primary X-ray flare data collection')

    # Fetch from NOAA, with safeguards if the service is down
    try:
        raw_data = fetch_json(URL_7DAY, logfiles_path, SOURCE)
    except RuntimeError as error:
        log_error(logfiles_path, SOURCE, str(error))
        log_message(logfiles_path, SOURCE,
                    'Abandoned GOES primary X-ray flare data collection - '
                    'NOAA service unavailable (see logerror.log)')
        return 1

    if not isinstance(raw_data, list):
        log_error(logfiles_path, SOURCE,
                  f'Unexpected response from {URL_7DAY}')
        log_message(logfiles_path, SOURCE,
                    'Abandoned GOES primary X-ray flare data collection - '
                    'unusable response (see logerror.log)')
        return 1

    # An empty list is valid - no flares in the last 7 days
    days, skipped = events_by_day(raw_data)
    if skipped:
        log_message(logfiles_path, SOURCE,
                    f'Skipped {skipped} flare records without a begin time')

    changed = upsert_events(data_path, days)
    if changed:
        for path, (added, updated) in sorted(changed.items()):
            log_message(logfiles_path, SOURCE,
                        f'Added {added} and updated {updated} '
                        f'flare events in {path}')
    else:
        log_message(logfiles_path, SOURCE,
                    'No new or revised flare events')

    log_message(logfiles_path, SOURCE,
                'Completed GOES primary X-ray flare data collection')
    return 0


if __name__ == '__main__':
    sys.exit(main())
