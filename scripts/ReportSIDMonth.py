#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to produce the monthly SID report for the BAA Radio Astronomy
# Group from the reviewed candidate events written by ExtractSIDEvents.py
# (<data>/SID_events/<CALLSIGN>/YYYY/YYYY-MM.csv - see that script and the
# README for the review workflow).
#
# Run manually after reviewing the month's candidates:
#   ReportSIDMonth.py                        report last month, all stations
#   ReportSIDMonth.py --month 2026-05        report a specific month
#   ReportSIDMonth.py --callsign DHO38       one station only
#   ReportSIDMonth.py --email                also email the report CSV to
#                                            the BAA coordinator (requires
#                                            send_enabled = true in
#                                            config/baa-report.ini)
#   ReportSIDMonth.py --email-self           email the report CSV to the
#                                            [email] "to" list in
#                                            config/alerts.ini instead
#                                            (e.g. to finish it on a PC)
#
# Only rows the observer has set to "reviewed" are included; rows still
# in the "candidate" status are listed as a warning and excluded, and
# "rejected" rows are ignored. The observer's obs_* values are used where
# filled in, falling back to the automatic est_* values. The importance
# is recalculated from the final start/end times using the duration-based
# SID scale, unless the observer entered an explicit obs_importance; an
# unknown end time is reported as "?" with an importance of "-".
#
# The report is written as a CSV (observer/station details followed by the
# BAA five-field table: Day, Class, Start, Peak, End, Importance - all
# times UTC) to:
#   <data>/SID_events/<CALLSIGN>/YYYY/BAA_<CALLSIGN>_YYYY-MM.csv
# A month with no reviewed events still produces a report (a nil return).
#
# Emailing uses the [smtp] settings in config/alerts.ini (shared with the
# flare alert emails; see install/alerts.ini.example). The report is never
# emailed automatically - submission is a deliberate, manual act.
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
import csv
import os
import sys
from datetime import datetime, timedelta
from email.message import EmailMessage

from vlf_common import (load_aerials, load_paths, load_user, log_error,
                        log_message, utc_now)
from vlf_mail import attach_file, load_smtp_settings, send_message
from vlf_sid import (END_UNKNOWN, IMPORTANCE_UNKNOWN, STATUS_CANDIDATE,
                     STATUS_REVIEWED, candidates_file,
                     importance_from_minutes, load_baa_settings,
                     read_candidates)

SOURCE = 'ReportSIDMonth.py'

TABLE_HEADER = ['Day', 'Class', 'Start', 'Peak', 'End', 'Importance']


# ==========================================================================================
#
# Report rows
#
# ==========================================================================================

def parse_minutes(start_text, end_text):
    """Duration start->end in minutes (times "HH:MM", an event may end
    after midnight), or None when the end is unknown/unreadable."""
    try:
        start = datetime.strptime(start_text, '%H:%M')
        end = datetime.strptime(end_text, '%H:%M')
    except ValueError:
        return None
    if end < start:
        end += timedelta(days=1)
    return (end - start).total_seconds() / 60


def report_row(candidate):
    """The five-field BAA table row for one reviewed candidate.

    Observer (obs_*) values override the automatic estimates; the
    importance is recalculated from the final times unless the observer
    entered one explicitly."""
    start = candidate['obs_start'] or candidate['est_start']
    peak = candidate['obs_peak'] or candidate['est_peak']
    end = candidate['obs_end'] or candidate['est_end']
    importance = candidate['obs_importance']
    if not importance:
        if end == END_UNKNOWN:
            importance = IMPORTANCE_UNKNOWN
        else:
            minutes = parse_minutes(start, end)
            importance = (importance_from_minutes(minutes) if minutes
                          else candidate['est_importance']
                          or IMPORTANCE_UNKNOWN)
    day = candidate['date'].split('-')[2].lstrip('0') or '0'
    return [day, candidate['goes_class'], start, peak, end, importance]


def select_rows(candidates):
    """Split the month's candidates into (reviewed, unreviewed) lists;
    rejected rows are dropped."""
    reviewed = []
    unreviewed = []
    for candidate in candidates:
        status = candidate['status'].lower()
        if status == STATUS_REVIEWED:
            reviewed.append(candidate)
        elif status == STATUS_CANDIDATE:
            unreviewed.append(candidate)
    return reviewed, unreviewed


# ==========================================================================================
#
# Report file
#
# ==========================================================================================

def report_file(data_path, callsign, month):
    year = month.split('-')[0]
    return os.path.join(data_path, 'SID_events', callsign, year,
                        f'BAA_{callsign}_{month}.csv')


def metadata_lines(settings, user, station, month):
    """The observer/station details at the top of the report."""
    khz = station['frequency_hz'] / 1000
    lines = [
        ['BAA Radio Astronomy Group - VLF SID monthly report'],
        ['Month', month],
        ['Observer', settings['observer_name']],
    ]
    if settings['baa_member_no']:
        lines.append(['BAA membership no.', settings['baa_member_no']])
    if user['name']:
        lines.append(['Location', user['name']])
    lines.append(['Transmitter', station['callsign']])
    lines.append(['Frequency (kHz)', f'{khz:g}'])
    if settings['equipment']:
        lines.append(['Equipment', settings['equipment']])
    lines.append(['All times UTC', ''])
    return lines


def write_report(path, metadata, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='') as report:
        writer = csv.writer(report)
        writer.writerows(metadata)
        writer.writerow([])
        writer.writerow(TABLE_HEADER)
        if rows:
            writer.writerows(rows)
        else:
            writer.writerow(['No SID events observed this month'])


def report_text(metadata, rows):
    """Plain-text version of the report for the email body."""
    lines = [' : '.join(str(field) for field in line if field != '')
             for line in metadata]
    lines.append('')
    if not rows:
        lines.append('  '.join(TABLE_HEADER))
        lines.append('No SID events observed this month')
        return '\n'.join(lines) + '\n'
    table = [TABLE_HEADER] + [[str(field) for field in row]
                              for row in rows]
    widths = [max(len(row[index]) if index < len(row) else 0
                  for row in table)
              for index in range(len(TABLE_HEADER))]
    for row in table:
        lines.append('  '.join(field.ljust(width) for field, width
                               in zip(row, widths)).rstrip())
    return '\n'.join(lines) + '\n'


# ==========================================================================================
#
# Email
#
# ==========================================================================================

def email_report(settings, smtp, recipients, station, month, path, body,
                 logfiles_path):
    """Email the report CSV. Returns True on success."""
    message = EmailMessage()
    message['Subject'] = (f'VLF SID report {month} - {station["callsign"]} '
                          f'- {settings["observer_name"]}')
    message['From'] = smtp['email_from']
    message['To'] = ', '.join(recipients)
    message.set_content(body)
    if not attach_file(message, path):
        log_error(logfiles_path, SOURCE,
                  f'Could not attach {path} to the report email')
        return False
    success, error = send_message(smtp, message)
    if not success:
        log_error(logfiles_path, SOURCE,
                  f'Failed to email the report for {station["callsign"]} '
                  f'{month}: {error}')
    return success


def resolve_recipients(arguments, settings, smtp):
    """The recipient list for --email/--email-self, or an error string."""
    if arguments.email_self:
        recipients = [address.strip() for address
                      in smtp['email_to'].split(',') if address.strip()]
        if not recipients:
            return None, ('no [email] "to" addresses configured in '
                          'alerts.ini for --email-self')
        return recipients, ''
    if not settings['send_enabled']:
        return None, ('sending to the coordinator is disabled - set '
                      'send_enabled = true in config/baa-report.ini '
                      'once the report has been reviewed')
    if not settings['coordinator_email']:
        return None, ('no coordinator_email configured in '
                      'config/baa-report.ini')
    recipients = [settings['coordinator_email']]
    if settings['cc_self']:
        recipients += [address.strip() for address
                       in smtp['email_to'].split(',') if address.strip()]
    return recipients, ''


# ==========================================================================================
#
# Main
#
# ==========================================================================================

def previous_month():
    first_of_month = utc_now().date().replace(day=1)
    last_month = first_of_month - timedelta(days=1)
    return f'{last_month:%Y-%m}'


def main():
    parser = argparse.ArgumentParser(
        description='Produce the monthly BAA SID report from the reviewed '
                    'candidate events')
    parser.add_argument('--month', metavar='YYYY-MM',
                        help='month to report (default: last month)')
    parser.add_argument('--callsign',
                        help='report one station only (default: all '
                             'configured stations)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--email', action='store_true',
                       help='email the report to the BAA coordinator')
    group.add_argument('--email-self', action='store_true',
                       help='email the report to yourself (the alerts.ini '
                            '[email] "to" list)')
    arguments = parser.parse_args()

    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    month = arguments.month or previous_month()
    try:
        datetime.strptime(month, '%Y-%m')
    except ValueError:
        print(f'Invalid --month "{month}" - expected YYYY-MM')
        return 1

    stations = load_aerials()['stations']
    if arguments.callsign:
        stations = [station for station in stations
                    if station['callsign'].lower()
                    == arguments.callsign.lower()]
        if not stations:
            print(f'Callsign "{arguments.callsign}" is not configured '
                  'in aerials.ini')
            return 1
    if not stations:
        print('No aerials configured in aerials.ini - nothing to report')
        return 1

    settings = load_baa_settings()
    if not settings['observer_name']:
        print('Warning: no observer name set in config/baa-report.ini')
    user = load_user()

    smtp = recipients = None
    if arguments.email or arguments.email_self:
        smtp = load_smtp_settings()
        recipients, error = resolve_recipients(arguments, settings, smtp)
        if recipients is None:
            print(f'Report not emailed: {error}')
            return 1

    log_message(logfiles_path, SOURCE, f'Started SID report for {month}')
    failures = 0
    for station in stations:
        callsign = station['callsign']
        candidates = read_candidates(
            candidates_file(data_path, callsign, month))
        reviewed, unreviewed = select_rows(candidates)

        if unreviewed:
            print(f'{callsign}: WARNING - {len(unreviewed)} candidate '
                  f'event(s) not yet reviewed and NOT included:')
            for candidate in unreviewed:
                print(f'  {candidate["date"]} flare {candidate["goes_class"]}'
                      f' at {candidate["goes_begin"]} '
                      f'(est. SID {candidate["est_start"]}-'
                      f'{candidate["est_end"]})')
            log_message(logfiles_path, SOURCE,
                        f'{callsign}: {len(unreviewed)} unreviewed '
                        f'candidate(s) excluded from the {month} report')

        rows = [report_row(candidate) for candidate in reviewed]
        metadata = metadata_lines(settings, user, station, month)
        path = report_file(data_path, callsign, month)
        try:
            write_report(path, metadata, rows)
        except OSError as error:
            print(f'{callsign}: failed to write the report: {error}')
            log_error(logfiles_path, SOURCE,
                      f'Failed to write {path}: {error}')
            failures += 1
            continue

        body = report_text(metadata, rows)
        print(f'{callsign}: {len(rows)} reviewed event(s) written '
              f'to {path}')
        print()
        print(body)
        log_message(logfiles_path, SOURCE,
                    f'{callsign}: wrote the {month} report '
                    f'({len(rows)} event(s)) to {path}')

        if recipients:
            if email_report(settings, smtp, recipients, station, month,
                            path, body, logfiles_path):
                print(f'{callsign}: report emailed to '
                      f'{", ".join(recipients)}')
                log_message(logfiles_path, SOURCE,
                            f'{callsign}: {month} report emailed to '
                            f'{", ".join(recipients)}')
            else:
                print(f'{callsign}: FAILED to email the report - '
                      'see logfiles/logerror.log')
                failures += 1

    log_message(logfiles_path, SOURCE, f'Completed SID report for {month}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
