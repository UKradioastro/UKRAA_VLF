#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to upload the plot images and the plots.json manifest to an
# external web site by FTP, configured in config/remote-upload.ini (see
# install/remote-upload.ini.example). The remote folder layout mirrors
# the local temp folder, so the same WWW/index.html works unchanged on
# the remote site (upload index.html and the images folder there once,
# manually):
#
#   <directory>/temp/plots.json
#   <directory>/temp/rolling/day|3day|7day/<frequency_hz>.png
#   <directory>/temp/periods/yesterday|3day|7day/<frequency_hz>.png
#
# Two modes, intended to be run from cron shortly after the matching
# plot scripts (see install/crontabVLF.cron):
#
#   rolling [--days 1|3|7] : the rolling plots for that window
#                            (every 5 minutes for the 24-hour plots,
#                            hourly for the 3/7-day plots)
#   periods                : the midnight-aligned yesterday/3-day/7-day
#                            plots (daily, after PlotDataPeriod.py)
#
# Both modes also refresh temp/plots.json on the remote site (uploaded
# last, so the manifest never references an image that is not there yet).
# Plot types disabled in config/plots.ini are skipped.
#
# While uploads are disabled (enabled = false, or no remote-upload.ini)
# the script exits quietly, so the cron entries can stay in place.
#
# Supports plain FTP and explicit FTPS (tls = true) - many hosts without
# SFTP still offer FTPS, which encrypts the password and the transfers.
#
# All times are UTC. Activity is logged to logfiles/logfile.log; failures
# are logged to logfiles/logerror.log (with credentials redacted).
#
# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

import argparse
import configparser
import ftplib
import os
import posixpath
import sys

from vlf_common import (CONFIG_FILE, load_paths, load_plot_options,
                        log_error, log_message)

SOURCE = 'UploadDataWWW.py'

REMOTE_UPLOAD_FILE = os.path.join(os.path.dirname(CONFIG_FILE),
                                  'remote-upload.ini')

# plots.ini section and temp subfolder for each rolling window
ROLLING_WINDOWS = {
    1: {'section': 'rolling', 'folder': 'day', 'label': '24-hour'},
    3: {'section': '3day', 'folder': '3day', 'label': '3-day'},
    7: {'section': '7day', 'folder': '7day', 'label': '7-day'},
}

# plots.ini section and temp subfolder for each midnight-aligned plot type
PERIOD_FOLDERS = (
    ('yesterday', 'yesterday'),
    ('3day', '3day'),
    ('7day', '7day'),
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Upload the plot images and plots.json manifest to an '
                    'external web site by FTP.')
    parser.add_argument('mode', choices=('rolling', 'periods'),
                        help='rolling: the rolling plots; periods: the '
                             'midnight-aligned yesterday/3-day/7-day plots')
    parser.add_argument('--days', type=int, choices=sorted(ROLLING_WINDOWS),
                        default=1,
                        help='rolling window to upload (default 1; '
                             'ignored in periods mode)')
    return parser.parse_args()


def load_settings():
    """Return the remote-upload.ini [ftp] settings, or None when uploads
    are not configured/enabled (the quiet do-nothing case)."""
    if not os.path.isfile(REMOTE_UPLOAD_FILE):
        return None
    parser = configparser.ConfigParser()
    parser.read(REMOTE_UPLOAD_FILE)
    if not parser.getboolean('ftp', 'enabled', fallback=False):
        return None
    return {
        'site': parser.get('ftp', 'site', fallback='').strip(),
        'user': parser.get('ftp', 'user', fallback='').strip(),
        'password': parser.get('ftp', 'password', fallback='').strip(),
        'port': parser.getint('ftp', 'port', fallback=21),
        'directory': parser.get('ftp', 'directory', fallback='/').strip(),
        'timeout_seconds': parser.getint('ftp', 'timeout_seconds',
                                         fallback=30),
        'passive': parser.getboolean('ftp', 'passive', fallback=True),
        'create_dirs': parser.getboolean('ftp', 'create_dirs',
                                         fallback=True),
        'tls': parser.getboolean('ftp', 'tls', fallback=False),
    }


def redact(text, settings):
    """Remove the FTP credentials from an error message before logging."""
    redacted = str(text)
    for key, label in (('user', '[redacted-user]'),
                       ('password', '[redacted-password]')):
        if settings[key]:
            redacted = redacted.replace(settings[key], label)
    return redacted


def ensure_remote_dir(ftp, remote_dir, create_dirs, known_dirs):
    """Change to remote_dir, creating missing folders when configured.
    known_dirs caches folders already visited this session."""
    if remote_dir in known_dirs:
        ftp.cwd(remote_dir)
        return
    if not create_dirs:
        ftp.cwd(remote_dir)
        known_dirs.add(remote_dir)
        return
    ftp.cwd('/')
    for part in remote_dir.split('/'):
        if not part:
            continue
        try:
            ftp.cwd(part)
        except ftplib.error_perm:
            ftp.mkd(part)
            ftp.cwd(part)
    known_dirs.add(remote_dir)


def folder_entries(local_folder, remote_folder):
    """(local path, remote folder, filename) for each PNG in a temp
    subfolder, or an empty list if the folder does not exist."""
    if not os.path.isdir(local_folder):
        return []
    return [(os.path.join(local_folder, name), remote_folder, name)
            for name in sorted(os.listdir(local_folder))
            if name.endswith('.png')
            and os.path.isfile(os.path.join(local_folder, name))]


def collect_uploads(mode, days, paths, remote_base, logfiles_path):
    """Return the (local path, remote folder, filename) upload list for
    the requested mode, ending with plots.json, or None when there is
    nothing to do (plot type disabled)."""
    temp_path = paths['temp']
    remote_temp = posixpath.join(remote_base, 'temp')
    options = load_plot_options()
    entries = []

    if mode == 'rolling':
        window = ROLLING_WINDOWS[days]
        if not options[window['section']]['enabled']:
            log_message(logfiles_path, SOURCE,
                        f'Rolling {window["label"]} plots disabled in '
                        f'plots.ini - nothing to upload')
            return None
        entries.extend(folder_entries(
            os.path.join(temp_path, 'rolling', window['folder']),
            posixpath.join(remote_temp, 'rolling', window['folder'])))
    else:
        for section, folder in PERIOD_FOLDERS:
            if not options[section]['enabled']:
                continue
            entries.extend(folder_entries(
                os.path.join(temp_path, 'periods', folder),
                posixpath.join(remote_temp, 'periods', folder)))

    # Manifest last, so it never references an image not yet uploaded
    manifest_path = os.path.join(temp_path, 'plots.json')
    if os.path.isfile(manifest_path):
        entries.append((manifest_path, remote_temp, 'plots.json'))
    else:
        log_error(logfiles_path, SOURCE,
                  f'Manifest not found: {manifest_path} - not uploaded')
    return entries


def upload(settings, entries, logfiles_path):
    """Upload the collected files over one FTP(S) connection. Returns the
    number of files uploaded, or None on failure."""
    ftp_class = ftplib.FTP_TLS if settings['tls'] else ftplib.FTP
    known_dirs = set()
    uploaded = 0
    try:
        with ftp_class() as ftp:
            ftp.connect(settings['site'], settings['port'],
                        timeout=settings['timeout_seconds'])
            ftp.login(user=settings['user'], passwd=settings['password'])
            if settings['tls']:
                ftp.prot_p()
            ftp.set_pasv(settings['passive'])
            for local_path, remote_folder, name in entries:
                ensure_remote_dir(ftp, remote_folder,
                                  settings['create_dirs'], known_dirs)
                with open(local_path, 'rb') as upload_file:
                    ftp.storbinary(f'STOR {name}', upload_file)
                uploaded += 1
    except ftplib.all_errors as error:  # includes OSError/timeouts
        log_error(logfiles_path, SOURCE,
                  f'FTP upload failed after {uploaded} file(s): '
                  f'{redact(error, settings)}')
        return None
    return uploaded


def main():
    args = parse_args()
    paths = load_paths()
    logfiles_path = paths['logfiles']

    settings = load_settings()
    if settings is None:
        # Not configured/enabled - exit quietly so the cron entries can
        # stay in place before remote upload is set up
        return 0

    if not (settings['site'] and settings['user'] and settings['password']
            and settings['directory']):
        log_error(logfiles_path, SOURCE,
                  f'FTP settings incomplete in {REMOTE_UPLOAD_FILE} '
                  f'(need site, user, password, directory)')
        return 1

    remote_base = settings['directory'].rstrip('/') or '/'
    label = (f'rolling {ROLLING_WINDOWS[args.days]["label"]}'
             if args.mode == 'rolling' else 'period')

    entries = collect_uploads(args.mode, args.days, paths, remote_base,
                              logfiles_path)
    if entries is None:
        return 0
    if not entries:
        log_error(logfiles_path, SOURCE,
                  f'No {label} plots found to upload - plots not '
                  f'produced yet?')
        return 1

    log_message(logfiles_path, SOURCE,
                f'Started {label} upload to {settings["site"]} '
                f'({len(entries)} file(s))')
    uploaded = upload(settings, entries, logfiles_path)
    if uploaded is None:
        return 1
    log_message(logfiles_path, SOURCE,
                f'Completed {label} upload - {uploaded} file(s) uploaded')
    return 0


if __name__ == '__main__':
    sys.exit(main())
