#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Shared email helpers for the UKRAA VLF scripts (EvaluateAlerts.py and
# ReportSIDMonth.py):
#
#   - loading the outgoing mail settings ([smtp] and [email] sections)
#     from config/alerts.ini, so the SMTP server is configured once
#   - sending a prepared email.message.EmailMessage through that server
#   - attaching files to a message with a sensible MIME type
#
# ==========================================================================================

import configparser
import mimetypes
import os
import smtplib

from vlf_common import CONFIG_FILE, parse_bool

ALERTS_FILE = os.path.join(os.path.dirname(CONFIG_FILE), 'alerts.ini')

SMTP_TIMEOUT = 30           # seconds


def load_smtp_settings():
    """Return the [smtp] and [email] settings from alerts.ini.

    Keys returned: smtp_host, smtp_port, smtp_user, smtp_password,
    smtp_starttls, smtp_ssl, email_from, email_to.
    """
    parser = configparser.ConfigParser()
    parser.read(ALERTS_FILE)

    def get(section, option, fallback=''):
        return parser.get(section, option, fallback=fallback).strip()

    try:
        smtp_port = int(get('smtp', 'port', '587'))
    except ValueError:
        smtp_port = 587

    return {
        'smtp_host': get('smtp', 'host'),
        'smtp_port': smtp_port,
        'smtp_user': get('smtp', 'username'),
        'smtp_password': get('smtp', 'password'),
        'smtp_starttls': parse_bool(get('smtp', 'starttls'), True),
        'smtp_ssl': parse_bool(get('smtp', 'ssl'), False),
        'email_from': get('email', 'from'),
        'email_to': get('email', 'to'),
    }


def attach_file(message, path):
    """Attach a file to an EmailMessage, guessing the MIME type from the
    filename (e.g. .png -> image/png, .csv -> text/csv). Returns True on
    success, False if the file could not be read."""
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    maintype, subtype = mime_type.split('/', 1)
    try:
        with open(path, 'rb') as attachment:
            message.add_attachment(attachment.read(), maintype=maintype,
                                   subtype=subtype,
                                   filename=os.path.basename(path))
    except OSError:
        return False
    return True


def send_message(settings, message):
    """Send a prepared EmailMessage using the given SMTP settings
    (the keys returned by load_smtp_settings).

    Returns (success, error_text).
    """
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
