#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to get the sunrise and sunset times (UTC) for a given day from the
# sunrise-sunset.org API:
#   https://api.sunrise-sunset.org/json?lat=<lat>&lng=<lng>&date=<date>&formatted=0
#
# NOTE: attribution to https://sunrise-sunset.org is required by the API
# terms of use.
#
# The station latitude/longitude (and name) are read from the [location]
# section of config/user.ini - see install/user.ini.example.
#
# Intended to be run from cron once an hour. If the day's file already
# exists the program exits immediately without logging or contacting the
# API, so the data is normally fetched by the first run after 00:00 UTC
# and the remaining runs are free retries after a network outage.
# Both times are stored in a SINGLE daily file:
#   <data>/Sun/YYYY/YYYY-MM/YYYY-MM-DD.csv
# containing one record:
#   yyyy-mm-dd hh:mm:ss,sunrise,yyyy-mm-dd hh:mm:ss,sunset
#
# Usage:
#   GetDataSun.py                     today's times (skipped if already stored)
#   GetDataSun.py --date 2026-11-20   backfill a specific (past) day
#   GetDataSun.py --force             re-fetch and rewrite even if stored
#
# All timestamps (data, log entries) are UTC.
#
# Activity is logged to logfiles/logfile.log; failures (service down,
# missing lat/long, bad response, etc.) are logged to logfiles/logerror.log.
#
# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

import argparse
import os
import sys
from datetime import datetime, timezone

from vlf_common import (USER_FILE, fetch_json, load_paths, load_user,
                        log_error, log_message, utc_now)

SOURCE = 'GetDataSun.py'

API_URL = ('https://api.sunrise-sunset.org/json'
           '?lat={latitude}&lng={longitude}&date={date}&formatted=0')

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def day_file_path(data_path, day):
    """Path of the daily sun file: <data>/Sun/YYYY/YYYY-MM/YYYY-MM-DD.csv"""
    return os.path.join(data_path, 'Sun', f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def parse_api_time(text):
    """ISO 8601 time from the API -> aware UTC datetime, or None."""
    try:
        when = datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None
    return when.astimezone(timezone.utc)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Fetch sunrise/sunset times from sunrise-sunset.org')
    parser.add_argument(
        '--date', metavar='YYYY-MM-DD',
        help='day to fetch (default: today, UTC) - use to backfill a '
             'missed day')
    parser.add_argument(
        '--force', action='store_true',
        help='re-fetch and rewrite the file even if the day is already '
             'stored')
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    if arguments.date:
        try:
            day = datetime.strptime(arguments.date, '%Y-%m-%d').date()
        except ValueError:
            print(f'Bad --date value (expected YYYY-MM-DD): '
                  f'{arguments.date}', file=sys.stderr)
            return 1
    else:
        day = utc_now().date()

    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    # Already stored? Nothing to do (hourly cron runs are retries, so exit
    # quietly without flooding the log)
    path = day_file_path(data_path, day)
    if os.path.isfile(path) and not arguments.force:
        return 0

    log_message(logfiles_path, SOURCE,
                f'Started sunrise/sunset data collection for {day:%Y-%m-%d}')

    user = load_user()
    if user['latitude'] is None or user['longitude'] is None:
        log_error(logfiles_path, SOURCE,
                  f'Latitude/longitude not configured - set the [location] '
                  f'section in {USER_FILE}')
        log_message(logfiles_path, SOURCE,
                    'Abandoned sunrise/sunset data collection - '
                    'no location configured (see logerror.log)')
        return 1

    url = API_URL.format(latitude=user['latitude'],
                         longitude=user['longitude'],
                         date=f'{day:%Y-%m-%d}')

    # Fetch from the API, with safeguards if the service is down
    try:
        data = fetch_json(url, logfiles_path, SOURCE)
    except RuntimeError as error:
        log_error(logfiles_path, SOURCE, str(error))
        log_message(logfiles_path, SOURCE,
                    'Abandoned sunrise/sunset data collection - '
                    'service unavailable (see logerror.log)')
        return 1

    results = data.get('results', {}) if isinstance(data, dict) else {}
    sunrise = parse_api_time(results.get('sunrise'))
    sunset = parse_api_time(results.get('sunset'))
    if data.get('status') != 'OK' or sunrise is None or sunset is None:
        log_error(logfiles_path, SOURCE,
                  f'Unusable response from sunrise-sunset.org '
                  f'(status: {data.get("status") if isinstance(data, dict) else "?"})')
        log_message(logfiles_path, SOURCE,
                    'Abandoned sunrise/sunset data collection - '
                    'unusable response (see logerror.log)')
        return 1

    # Write both times to a single daily file (rewritten - re-run safe)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as data_file:
        data_file.write(f'{sunrise:{TIME_FORMAT}},sunrise,'
                        f'{sunset:{TIME_FORMAT}},sunset\n')

    station = f' for {user["name"]}' if user['name'] else ''
    log_message(logfiles_path, SOURCE,
                f'Stored sunrise {sunrise:%H:%M:%S} UTC and sunset '
                f'{sunset:%H:%M:%S} UTC{station} in {path}')
    log_message(logfiles_path, SOURCE,
                'Completed sunrise/sunset data collection')
    return 0


if __name__ == '__main__':
    sys.exit(main())
