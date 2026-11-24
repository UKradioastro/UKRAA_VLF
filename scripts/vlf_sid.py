#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Shared helpers for the BAA SID reporting scripts (ExtractSIDEvents.py
# and ReportSIDMonth.py):
#
#   - loading config/baa-report.ini (observer details, report/email
#     settings and the candidate-detection tuning values)
#   - the SID importance scale (duration based, per the UKRAA VLF
#     Receiver Manual / BAA Radio Astronomy Group convention)
#   - reading and writing the monthly SID candidates file:
#         <data>/SID_events/<CALLSIGN>/YYYY/YYYY-MM.csv
#
# The candidates file is a normal CSV with a header row, designed to be
# reviewed and edited by the observer (see install/baa-report.ini.example
# and the README). The est_* columns hold the automatic estimates and are
# never overwritten once the row leaves the "candidate" status; the obs_*
# columns hold the observer's confirmed/corrected values.
#
# All times are UTC.
#
# ==========================================================================================

import configparser
import csv
import json
import os

from vlf_common import CONFIG_FILE, TIME_FORMAT, parse_bool, utc_now

BAA_REPORT_FILE = os.path.join(os.path.dirname(CONFIG_FILE),
                               'baa-report.ini')

# Candidate row statuses
STATUS_CANDIDATE = 'candidate'   # automatic estimate awaiting review
STATUS_REVIEWED = 'reviewed'     # confirmed by the observer -> reported
STATUS_REJECTED = 'rejected'     # dismissed by the observer -> not reported

# Columns of the monthly candidates CSV, in file order
FIELDNAMES = ['date', 'goes_begin', 'goes_class',
              'est_start', 'est_peak', 'est_end', 'est_importance',
              'obs_start', 'obs_peak', 'obs_end', 'obs_importance',
              'status', 'notes', 'plot']

# SID importance scale: duration start->end in minutes (UKRAA VLF Receiver
# Manual sections 28-32 / Hyde SID project). Unknown end -> '-'.
IMPORTANCE_SCALE = [(19, '1-'), (26, '1'), (33, '1+'), (46, '2'),
                    (86, '2+'), (126, '3')]
IMPORTANCE_LONGEST = '3+'
IMPORTANCE_UNKNOWN = '-'
END_UNKNOWN = '?'


def importance_from_minutes(minutes):
    """SID importance rating from the start->end duration in minutes,
    or '-' when the duration is unknown (None)."""
    if minutes is None:
        return IMPORTANCE_UNKNOWN
    for limit, rating in IMPORTANCE_SCALE:
        if minutes < limit:
            return rating
    return IMPORTANCE_LONGEST


def load_baa_settings():
    """Return the config/baa-report.ini settings with defaults.

    Keys returned:
      observer_name, baa_member_no, equipment     ([observer])
      coordinator_email, cc_self, send_enabled    ([report])
      pre_minutes, post_minutes, min_departure_v,
      noise_multiplier                            ([detection])
    """
    parser = configparser.ConfigParser()
    parser.read(BAA_REPORT_FILE)

    def get(section, option, fallback=''):
        return parser.get(section, option, fallback=fallback).strip()

    def get_number(section, option, fallback, converter):
        try:
            return converter(get(section, option))
        except ValueError:
            return fallback

    return {
        'observer_name': get('observer', 'name'),
        'baa_member_no': get('observer', 'baa_member_no'),
        'equipment': get('observer', 'equipment'),
        'coordinator_email': get('report', 'coordinator_email'),
        'cc_self': parse_bool(get('report', 'cc_self'), True),
        'send_enabled': parse_bool(get('report', 'send_enabled'), False),
        'pre_minutes': get_number('detection', 'pre_minutes', 15, int),
        'post_minutes': get_number('detection', 'post_minutes', 60, int),
        'min_departure_v': get_number('detection', 'min_departure_v',
                                      0.05, float),
        'noise_multiplier': get_number('detection', 'noise_multiplier',
                                       4.0, float),
    }


def candidates_file(data_path, callsign, month):
    """Path of the monthly SID candidates file:
        <data>/SID_events/<CALLSIGN>/YYYY/YYYY-MM.csv
    month is a "YYYY-MM" string."""
    year = month.split('-')[0]
    return os.path.join(data_path, 'SID_events', callsign, year,
                        f'{month}.csv')


def read_candidates(path):
    """Candidate rows from a monthly file as a list of dicts (FIELDNAMES
    keys, missing columns blank). Returns [] if the file does not exist."""
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, newline='') as candidates:
        for row in csv.DictReader(candidates):
            if not (row.get('date') or '').strip():
                continue
            rows.append({name: (row.get(name) or '').strip()
                         for name in FIELDNAMES})
    return rows


def write_candidates(path, rows):
    """Write the monthly candidates file (header + rows sorted by date
    and NOAA begin time), atomically."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + '.tmp'
    with open(temp_path, 'w', newline='') as candidates:
        writer = csv.DictWriter(candidates, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in sorted(rows,
                          key=lambda row: (row['date'], row['goes_begin'])):
            writer.writerow(row)
    os.replace(temp_path, path)


def temp_plot_name(callsign, row):
    """Filename of an event's review plot in <temp>/events/YYYY-MM/
    (written by ExtractSIDEvents.py), relative to the temp folder."""
    month = row['date'][:7]
    stamp = row['goes_begin'].replace(':', '')
    # Forward slashes: this is a URL path relative to temp
    return f'events/{month}/{callsign}-{row["date"]}-{stamp}.png'


def write_events_manifest(temp_path, data_path, stations, months):
    """Write <temp>/events.json describing the candidate SID events for
    the intranet web page (WWW/index.html).

    The manifest is rebuilt from the monthly candidates files for the
    given "YYYY-MM" months (normally the current and previous month), so
    it reflects the observer's latest review statuses. Each event carries
    the final values (the observer's obs_* corrections where entered,
    otherwise the automatic estimates). Written atomically so the browser
    never reads a half-written file.
    """
    station_entries = []
    for station in stations:
        events = []
        for month in sorted(set(months), reverse=True):
            path = candidates_file(data_path, station['callsign'], month)
            for row in read_candidates(path):
                events.append({
                    'date': row['date'],
                    'goes_begin': row['goes_begin'],
                    'goes_class': row['goes_class'],
                    'start': row['obs_start'] or row['est_start'],
                    'peak': row['obs_peak'] or row['est_peak'],
                    'end': row['obs_end'] or row['est_end'],
                    'importance': (row['obs_importance']
                                   or row['est_importance']),
                    'status': row['status'],
                    'notes': row['notes'],
                    'plot': temp_plot_name(station['callsign'], row),
                })
        events.sort(key=lambda event: (event['date'], event['goes_begin']),
                    reverse=True)
        station_entries.append({
            'callsign': station['callsign'],
            'frequency_hz': station['frequency_hz'],
            'events': events,
        })

    manifest = {
        'generated_utc': f'{utc_now():{TIME_FORMAT}}',
        'months': sorted(set(months), reverse=True),
        'stations': station_entries,
    }
    os.makedirs(temp_path, exist_ok=True)
    manifest_path = os.path.join(temp_path, 'events.json')
    temp_file = manifest_path + '.tmp'
    with open(temp_file, 'w') as output:
        json.dump(manifest, output, indent=2)
        output.write('\n')
    os.replace(temp_file, manifest_path)
