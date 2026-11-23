#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to send email alerts for GOES X-ray solar flares and a daily
# heartbeat email, configured in config/alerts.ini (see
# install/alerts.ini.example).
#
# Intended to be run from cron every 5 minutes, offset after the NOAA
# flare data fetch and the rolling plots (3-59/5).
#
# Flare alerts:
#   Reads yesterday's and today's flare files written by
#   GetDataNOAAxrayFlares.py (<data>/NOAA_xray_flares/...). A flare whose
#   reported class reaches the configured flare_threshold (e.g. C1.0)
#   triggers one alert email. NOAA revises flare events in place while
#   they are in progress, so a follow-up email is sent if a flare is
#   later upgraded to a higher class letter (e.g. M -> X). State is kept
#   in <data>/alerts/alert-state.json so each flare alerts once per class
#   letter; a failed send is retried on the next run.
#
# Heartbeat:
#   One daily health-check email, attempted once per UTC day at/after the
#   configured hour, summarising the last 24 hours of flare activity and
#   whether the rolling plots are fresh.
#
# The current rolling plot (one per configured station) can optionally be
# attached to alert and heartbeat emails (attach_plot settings).
#
# Command line options (for testing the SMTP settings, see also the
# install procedure):
#   --test-email      send a one-off SMTP test email and exit
#   --test-heartbeat  send a one-off heartbeat email immediately and exit
# Both ignore email_enabled and do not modify the alert state.
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
import configparser
import json
import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from vlf_common import (CONFIG_FILE, TIME_FORMAT, load_aerials, load_paths,
                        log_error, log_message, utc_now)

SOURCE = 'EvaluateAlerts.py'

ALERTS_FILE = os.path.join(os.path.dirname(CONFIG_FILE), 'alerts.ini')

SMTP_TIMEOUT = 30           # seconds
STATE_RETENTION_DAYS = 8    # matches the NOAA 7-day flare feed
PLOT_STALE_MINUTES = 15     # rolling plots refresh every 5 minutes

# GOES X-ray flare class letters: decade flux in W/m2 and severity rank
LETTER_FLUX = {'A': 1e-8, 'B': 1e-7, 'C': 1e-6, 'M': 1e-5, 'X': 1e-4}
LETTER_RANK = {'A': 0, 'B': 1, 'C': 2, 'M': 3, 'X': 4}

DEFAULT_THRESHOLD = 'C1.0'


# ==========================================================================================
#
# Configuration
#
# ==========================================================================================

def parse_flare_class(text):
    """Flare class string ("M2.5") -> (letter, flux W/m2), or None."""
    text = (text or '').strip().upper()
    if len(text) < 2 or text[0] not in LETTER_FLUX:
        return None
    try:
        multiplier = float(text[1:])
    except ValueError:
        return None
    if multiplier <= 0:
        return None
    return text[0], LETTER_FLUX[text[0]] * multiplier


def parse_bool(text, fallback):
    if text is None:
        return fallback
    return text.strip().lower() in ('1', 'true', 'yes', 'y', 'on')


def load_settings(logfiles_path):
    """Return the alerts.ini settings with sensible defaults."""
    parser = configparser.ConfigParser()
    parser.read(ALERTS_FILE)

    def get(section, option, fallback=''):
        return parser.get(section, option, fallback=fallback).strip()

    threshold_text = get('alerts', 'flare_threshold', DEFAULT_THRESHOLD)
    threshold = parse_flare_class(threshold_text)
    if threshold is None:
        log_error(logfiles_path, SOURCE,
                  f'Invalid flare_threshold "{threshold_text}" in '
                  f'{ALERTS_FILE} - using {DEFAULT_THRESHOLD}')
        threshold_text = DEFAULT_THRESHOLD
        threshold = parse_flare_class(DEFAULT_THRESHOLD)

    try:
        smtp_port = int(get('smtp', 'port', '587'))
    except ValueError:
        smtp_port = 587

    try:
        heartbeat_hour = min(23, max(0, int(get('heartbeat', 'hour_utc', '9'))))
    except ValueError:
        heartbeat_hour = 9

    return {
        'email_enabled': parse_bool(get('alerts', 'email_enabled'), False),
        'threshold_text': threshold_text.upper(),
        'threshold_letter': threshold[0],
        'threshold_flux': threshold[1],
        'smtp_host': get('smtp', 'host'),
        'smtp_port': smtp_port,
        'smtp_user': get('smtp', 'username'),
        'smtp_password': get('smtp', 'password'),
        'smtp_starttls': parse_bool(get('smtp', 'starttls'), True),
        'smtp_ssl': parse_bool(get('smtp', 'ssl'), False),
        'email_from': get('email', 'from'),
        'email_to': get('email', 'to'),
        'email_attach_plot': parse_bool(get('email', 'attach_plot'), False),
        'web_url': get('web', 'url'),
        'heartbeat_enabled': parse_bool(get('heartbeat', 'enabled'), False),
        'heartbeat_hour_utc': heartbeat_hour,
        'heartbeat_to': get('heartbeat', 'to'),
        'heartbeat_attach_plot': parse_bool(get('heartbeat', 'attach_plot'),
                                            False),
    }


# ==========================================================================================
#
# Flare data
#
# ==========================================================================================

def flare_file(data_path, day):
    return os.path.join(data_path, 'NOAA_xray_flares', f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def read_flares(data_path, days):
    """Flare records from the daily files for the given dates.

    Record format (fields blank if not yet reported by NOAA):
      begin,satellite,begin_class,max_time,max_class,max_flux,end,end_class

    Returns a list of dicts sorted by begin time.
    """
    flares = []
    for day in days:
        path = flare_file(data_path, day)
        if not os.path.isfile(path):
            continue
        with open(path) as data_file:
            for line in data_file:
                fields = line.strip().split(',')
                if len(fields) < 8 or not fields[0]:
                    continue
                flares.append({
                    'begin': fields[0],
                    'satellite': fields[1],
                    'begin_class': fields[2],
                    'max_time': fields[3],
                    'max_class': fields[4],
                    'max_flux': fields[5],
                    'end': fields[6],
                    'end_class': fields[7],
                })
    return sorted(flares, key=lambda flare: flare['begin'])


def flare_current_class(flare):
    """Highest class reported so far: (letter, class_text, flux) or None.

    Prefers the reported max_class/max_flux, falling back to begin_class
    while the flare has not yet peaked.
    """
    class_text = flare['max_class'] or flare['begin_class']
    parsed = parse_flare_class(class_text)
    if parsed is None:
        return None
    letter, flux = parsed
    try:
        flux = float(flare['max_flux'])
    except ValueError:
        pass
    return letter, class_text.upper(), flux


def parse_time(text):
    return datetime.strptime(text, TIME_FORMAT).replace(tzinfo=timezone.utc)


# ==========================================================================================
#
# Alert state
#
# ==========================================================================================

def state_file(data_path):
    return os.path.join(data_path, 'alerts', 'alert-state.json')


def load_state(path):
    try:
        with open(path) as state_json:
            state = json.load(state_json)
    except (OSError, ValueError):
        state = {}
    state.setdefault('flares', {})
    state.setdefault('heartbeat', {})
    return state


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + '.tmp'
    with open(temp_path, 'w') as state_json:
        json.dump(state, state_json, indent=2)
        state_json.write('\n')
    os.replace(temp_path, path)


def prune_state(state, now):
    """Drop flare entries older than the NOAA feed retention."""
    cutoff = now - timedelta(days=STATE_RETENTION_DAYS)
    for begin in list(state['flares']):
        try:
            if parse_time(begin) < cutoff:
                del state['flares'][begin]
        except ValueError:
            del state['flares'][begin]


# ==========================================================================================
#
# Email
#
# ==========================================================================================

def attachment_paths(temp_path, stations):
    """Rolling plot(s) to attach: one per configured station, or the
    X-ray only plot while no stations are configured (written to
    <temp>/rolling/day/ by PlotDataRolling.py)."""
    if stations:
        names = [f'{station["frequency_hz"]}.png' for station in stations]
    else:
        names = ['NOAA.png']
    folder = os.path.join(temp_path, 'rolling', 'day')
    return [os.path.join(folder, name) for name in names
            if os.path.isfile(os.path.join(folder, name))]


def send_email(settings, subject, body, attachments, to_override=''):
    """Send an email; returns (success, error_text)."""
    recipients = [address.strip() for address in
                  (to_override or settings['email_to']).split(',')
                  if address.strip()]
    if not (settings['smtp_host'] and settings['email_from'] and recipients):
        return False, 'SMTP configuration incomplete (need host, from, to)'

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = settings['email_from']
    message['To'] = ', '.join(recipients)
    message.set_content(body)

    for path in attachments:
        try:
            with open(path, 'rb') as image_file:
                message.add_attachment(image_file.read(), maintype='image',
                                       subtype='png',
                                       filename=os.path.basename(path))
        except OSError:
            continue

    try:
        if settings['smtp_ssl']:
            with smtplib.SMTP_SSL(settings['smtp_host'],
                                  settings['smtp_port'],
                                  timeout=SMTP_TIMEOUT) as server:
                if settings['smtp_user']:
                    server.login(settings['smtp_user'],
                                 settings['smtp_password'])
                server.send_message(message)
        else:
            with smtplib.SMTP(settings['smtp_host'], settings['smtp_port'],
                              timeout=SMTP_TIMEOUT) as server:
                if settings['smtp_starttls']:
                    server.starttls()
                if settings['smtp_user']:
                    server.login(settings['smtp_user'],
                                 settings['smtp_password'])
                server.send_message(message)
    except Exception as error:
        return False, str(error)
    return True, ''


def station_summary(stations):
    if not stations:
        return 'none configured (X-ray data only)'
    return ', '.join(f'{station["callsign"]} '
                     f'({station["frequency_hz"] / 1000:g} kHz)'
                     for station in stations)


def build_alert_email(flare, class_text, previous_class, settings, stations):
    upgraded = previous_class is not None
    if upgraded:
        subject = f'[UKRAA VLF] Solar flare upgraded - {class_text}'
    else:
        subject = f'[UKRAA VLF] Solar flare alert - {class_text}'

    lines = ['UKRAA VLF solar flare alert', '']
    if upgraded:
        lines.append(f'Flare upgraded to class {class_text} '
                     f'(previously alerted at {previous_class})')
    else:
        lines.append(f'Flare class: {class_text}')
    lines.extend([
        f'Begin (UTC): {flare["begin"]}',
        f'Maximum (UTC): {flare["max_time"] or "in progress"}',
        f'End (UTC): {flare["end"] or "in progress"}',
        f'Peak flux: {flare["max_flux"] or "not yet reported"} W/m2',
        f'Satellite: GOES-{flare["satellite"] or "unknown"}',
        '',
        f'Alert threshold: {settings["threshold_text"]}',
        f'Stations monitored: {station_summary(stations)}',
    ])
    if settings['web_url']:
        lines.extend(['', f'Web page: {settings["web_url"]}'])
    lines.extend([
        '',
        'The current rolling plot is attached when enabled '
        '(attach_plot in alerts.ini).',
    ])
    return subject, '\n'.join(lines)


def read_plot_freshness(temp_path, now):
    """Rolling plot freshness from plots.json: (text, generated_utc)."""
    try:
        with open(os.path.join(temp_path, 'plots.json')) as manifest_json:
            generated_text = json.load(manifest_json).get('generated_utc', '')
        generated = parse_time(generated_text)
    except (OSError, ValueError):
        return 'unknown (plots.json missing or unreadable)', 'unknown'
    age_minutes = (now - generated).total_seconds() / 60
    if age_minutes > PLOT_STALE_MINUTES:
        return (f'STALE - last refreshed {generated_text} UTC '
                f'({age_minutes:.0f} minutes ago)'), generated_text
    return f'fresh (last refreshed {generated_text} UTC)', generated_text


def build_heartbeat_email(settings, stations, flares, temp_path, now):
    """Daily heartbeat with a 24-hour flare summary and plot freshness."""
    window_start = now - timedelta(hours=24)
    recent = []
    for flare in flares:
        current = flare_current_class(flare)
        if current is None:
            continue
        try:
            begin = parse_time(flare['begin'])
        except ValueError:
            continue
        if begin >= window_start:
            recent.append((flare, current))

    above = [entry for entry in recent
             if entry[1][2] >= settings['threshold_flux']]
    largest = max(recent, key=lambda entry: entry[1][2], default=None)
    freshness, _ = read_plot_freshness(temp_path, now)

    subject = (f'[UKRAA VLF] Daily heartbeat - {len(recent)} flare(s) '
               f'in the last 24 hours')
    lines = [
        'UKRAA VLF daily heartbeat',
        '',
        f'Sent at (UTC): {now:{TIME_FORMAT}}',
        f'Stations monitored: {station_summary(stations)}',
        f'Rolling plots: {freshness}',
        '',
        f'Flares in the last 24 hours: {len(recent)}',
        f'At/above alert threshold {settings["threshold_text"]}: '
        f'{len(above)}',
    ]
    if largest:
        flare, (_, class_text, _) = largest
        lines.append(f'Largest: {class_text} beginning {flare["begin"]} UTC')
    for flare, (_, class_text, _) in above:
        lines.append(f'  {class_text} begin {flare["begin"]} '
                     f'max {flare["max_time"] or "in progress"} '
                     f'end {flare["end"] or "in progress"}')
    if settings['web_url']:
        lines.extend(['', f'Web page: {settings["web_url"]}'])
    lines.extend([
        '',
        'This is a daily health-check email to confirm the VLF alert '
        'pipeline is running.',
    ])
    return subject, '\n'.join(lines)


# ==========================================================================================
#
# Alert and heartbeat evaluation
#
# ==========================================================================================

def evaluate_flares(settings, state, flares, stations, temp_path,
                    logfiles_path):
    """Send an alert for each flare newly at/above the threshold, or newly
    upgraded to a higher class letter than previously alerted."""
    attachments = (attachment_paths(temp_path, stations)
                   if settings['email_attach_plot'] else [])

    for flare in flares:
        current = flare_current_class(flare)
        if current is None:
            continue
        letter, class_text, flux = current
        if flux < settings['threshold_flux']:
            continue

        entry = state['flares'].get(flare['begin'])
        if entry and LETTER_RANK[letter] <= LETTER_RANK.get(
                entry.get('letter'), -1):
            continue
        previous_class = entry.get('class') if entry else None

        if not settings['email_enabled']:
            # Record the flare so suppression is logged once, not every run
            state['flares'][flare['begin']] = {
                'letter': letter, 'class': class_text,
                'suppressed_utc': f'{utc_now():{TIME_FORMAT}}',
            }
            log_message(logfiles_path, SOURCE,
                        f'Alert email suppressed for {class_text} flare '
                        f'beginning {flare["begin"]} '
                        f'(email_enabled = false in alerts.ini)')
            continue

        subject, body = build_alert_email(flare, class_text, previous_class,
                                          settings, stations)
        success, error_text = send_email(settings, subject, body, attachments)
        if success:
            state['flares'][flare['begin']] = {
                'letter': letter, 'class': class_text,
                'sent_utc': f'{utc_now():{TIME_FORMAT}}',
            }
            log_message(logfiles_path, SOURCE,
                        f'Alert email sent for {class_text} flare '
                        f'beginning {flare["begin"]}')
        else:
            # Leave the state unchanged so the send is retried next run
            log_error(logfiles_path, SOURCE,
                      f'Alert email failed for {class_text} flare '
                      f'beginning {flare["begin"]}: {error_text}')


def maybe_send_heartbeat(settings, state, flares, stations, temp_path,
                         logfiles_path, now):
    """Attempt the daily heartbeat once per UTC day at/after hour_utc."""
    if not (settings['email_enabled'] and settings['heartbeat_enabled']):
        return
    if now.hour < settings['heartbeat_hour_utc']:
        return
    today = f'{now:%Y-%m-%d}'
    if state['heartbeat'].get('attempt_date_utc') == today:
        return

    state['heartbeat']['attempt_date_utc'] = today
    state['heartbeat']['attempt_utc'] = f'{now:{TIME_FORMAT}}'

    attachments = (attachment_paths(temp_path, stations)
                   if settings['heartbeat_attach_plot'] else [])
    subject, body = build_heartbeat_email(settings, stations, flares,
                                          temp_path, now)
    success, error_text = send_email(settings, subject, body, attachments,
                                     to_override=settings['heartbeat_to'])
    if success:
        state['heartbeat']['sent_date_utc'] = today
        state['heartbeat']['sent_utc'] = f'{now:{TIME_FORMAT}}'
        state['heartbeat']['error'] = ''
        log_message(logfiles_path, SOURCE,
                    'Daily heartbeat email sent successfully')
    else:
        state['heartbeat']['error'] = error_text
        log_error(logfiles_path, SOURCE,
                  f'Daily heartbeat email failed: {error_text}')


# ==========================================================================================
#
# Main
#
# ==========================================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Evaluate X-ray flare alerts and send SMTP '
                    'notifications.')
    parser.add_argument('--test-email', action='store_true',
                        help='send a one-off SMTP test email and exit '
                             '(ignores email_enabled and alert state)')
    parser.add_argument('--test-heartbeat', action='store_true',
                        help='send a one-off heartbeat email immediately '
                             'and exit (ignores schedule and state)')
    return parser.parse_args()


def main():
    args = parse_args()

    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']
    temp_path = paths['temp']

    settings = load_settings(logfiles_path)
    stations = load_aerials()['stations']
    now = utc_now()
    days = [now.date() - timedelta(days=1), now.date()]
    flares = read_flares(data_path, days)

    if args.test_email:
        attachments = (attachment_paths(temp_path, stations)
                       if settings['email_attach_plot'] else [])
        subject = '[UKRAA VLF] TEST email'
        body = '\n'.join([
            'This is a UKRAA VLF SMTP test email.',
            '',
            'If you received this message, your SMTP settings are working.',
            '',
            f'Alert threshold: {settings["threshold_text"]}',
            f'Stations monitored: {station_summary(stations)}',
        ])
        success, error_text = send_email(settings, subject, body, attachments)
        if success:
            log_message(logfiles_path, SOURCE,
                        'SMTP test email sent successfully')
            return 0
        log_error(logfiles_path, SOURCE,
                  f'SMTP test email failed: {error_text}')
        return 2

    if args.test_heartbeat:
        attachments = (attachment_paths(temp_path, stations)
                       if settings['heartbeat_attach_plot'] else [])
        subject, body = build_heartbeat_email(settings, stations, flares,
                                              temp_path, now)
        success, error_text = send_email(settings, subject, body, attachments,
                                         to_override=settings['heartbeat_to'])
        if success:
            log_message(logfiles_path, SOURCE,
                        'Heartbeat test email sent successfully')
            return 0
        log_error(logfiles_path, SOURCE,
                  f'Heartbeat test email failed: {error_text}')
        return 2

    log_message(logfiles_path, SOURCE, 'Started alert evaluation')

    state_path = state_file(data_path)
    state = load_state(state_path)

    evaluate_flares(settings, state, flares, stations, temp_path,
                    logfiles_path)
    maybe_send_heartbeat(settings, state, flares, stations, temp_path,
                         logfiles_path, now)
    prune_state(state, now)

    try:
        save_state(state_path, state)
    except OSError as error:
        log_error(logfiles_path, SOURCE,
                  f'Failed to save alert state: {error}')

    log_message(logfiles_path, SOURCE, 'Completed alert evaluation')
    return 0


if __name__ == '__main__':
    sys.exit(main())
