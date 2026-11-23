#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Shared helpers for the UKRAA VLF scripts:
#
#   - loading the [paths] section from the vlf.ini configuration file
#   - loading user settings (station name, latitude, longitude) from user.ini
#   - writing timestamped entries (all times UTC) to the shared log files:
#         logfiles/logfile.log   : normal activity
#         logfiles/logerror.log  : errors / failures
#   - fetching JSON from a web service with retries
#   - writing the plots.json manifest consumed by the intranet web page
#
# The configuration file location can be overridden with the VLF_CONFIG
# environment variable (useful for testing). user.ini is expected in the
# same folder as vlf.ini.
#
# ==========================================================================================

import configparser
import json
import os
import time
from datetime import datetime, timezone

import requests

DEFAULT_HOME = '/home/pi/UKRAA-VLF/'
CONFIG_FILE = os.environ.get(
    'VLF_CONFIG', os.path.join(DEFAULT_HOME, 'config', 'vlf.ini'))
USER_FILE = os.path.join(os.path.dirname(CONFIG_FILE), 'user.ini')
AERIALS_FILE = os.path.join(os.path.dirname(CONFIG_FILE), 'aerials.ini')
PLOTS_FILE = os.path.join(os.path.dirname(CONFIG_FILE), 'plots.ini')

LOGFILE_NAME = 'logfile.log'
LOGERROR_NAME = 'logerror.log'

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

USER_AGENT = 'UKRAA-VLF/1.0'
REQUEST_TIMEOUT = 30        # seconds per request
RETRIES = 3                 # attempts before giving up
RETRY_DELAY = 10            # seconds between attempts


def utc_now():
    """Current time as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def load_paths():
    """Return the [paths] settings from vlf.ini, with sensible defaults.

    Keys returned: home, data, logfiles, plots, scripts, temp.
    """
    parser = configparser.ConfigParser()
    parser.read(CONFIG_FILE)
    home = parser.get('paths', 'home', fallback=DEFAULT_HOME)
    return {
        'home': home,
        'data': parser.get('paths', 'data',
                           fallback=os.path.join(home, 'data')),
        'logfiles': parser.get('paths', 'logfiles',
                               fallback=os.path.join(home, 'logfiles')),
        'plots': parser.get('paths', 'plots',
                            fallback=os.path.join(home, 'plots')),
        'scripts': parser.get('paths', 'scripts',
                              fallback=os.path.join(home, 'scripts')),
        'temp': parser.get('paths', 'temp',
                           fallback=os.path.join(home, 'temp')),
    }


def format_log_entry(timestamp, source_name, message):
    return (f'{timestamp:%Y-%m-%d %H:%M:%S} UTC : '
            f'{source_name:<27} : {message}')


def _write_log(logfiles_path, filename, source_name, message):
    os.makedirs(logfiles_path, exist_ok=True)
    entry = format_log_entry(utc_now(), source_name, message)
    with open(os.path.join(logfiles_path, filename), 'a') as log_file:
        log_file.write(entry + '\n')


def log_message(logfiles_path, source_name, message):
    """Append an activity entry (UTC timestamp) to logfile.log."""
    _write_log(logfiles_path, LOGFILE_NAME, source_name, message)


def log_error(logfiles_path, source_name, message):
    """Append an error entry (UTC timestamp) to logerror.log."""
    _write_log(logfiles_path, LOGERROR_NAME, source_name, message)


def load_user():
    """Return the [location] settings from user.ini.

    Keys returned: name, latitude, longitude (latitude/longitude are None
    if not configured).
    """
    parser = configparser.ConfigParser()
    parser.read(USER_FILE)
    return {
        'name': parser.get('location', 'name', fallback=''),
        'latitude': parser.getfloat('location', 'latitude', fallback=None),
        'longitude': parser.getfloat('location', 'longitude', fallback=None),
    }


def load_aerials():
    """Return the ADC settings and configured stations from aerials.ini.

    Returns {'adc': {...}, 'stations': [...]} where each station is
    {'channel', 'callsign', 'frequency_hz', 'off_air'}. Channels with a
    blank callsign or frequency (no receiver connected) are omitted.
    """
    parser = configparser.ConfigParser()
    parser.read(AERIALS_FILE)

    def get_int(section, key, fallback):
        text = parser.get(section, key, fallback='').strip()
        try:
            return int(text)
        except ValueError:
            return fallback

    adc = {
        'address_1': parser.get('MCP3424', 'address_1', fallback='0x68'),
        'address_2': parser.get('MCP3424', 'address_2', fallback='0x69'),
        'resolution': get_int('MCP3424', 'resolution', 18),
        'mode': get_int('MCP3424', 'mode', 1),
        'gain': get_int('MCP3424', 'gain', 1),
        'samples': get_int('MCP3424', 'samples', 15),
        'trim': get_int('MCP3424', 'trim', 5),
    }

    stations = []
    for channel in range(1, 9):
        section = f'channel_{channel}'
        if not parser.has_section(section):
            continue
        callsign = parser.get(section, 'callsign', fallback='').strip()
        frequency_text = parser.get(section, 'frequency_hz',
                                    fallback='').strip()
        if not callsign or not frequency_text:
            continue
        try:
            frequency_hz = int(frequency_text)
        except ValueError:
            continue
        stations.append({
            'channel': channel,
            'callsign': callsign,
            'frequency_hz': frequency_hz,
            'off_air': parser.get(section, 'off_air', fallback='').strip(),
        })
    return {'adc': adc, 'stations': stations}


# Per-plot-type display options (config/plots.ini); the defaults preserve
# the original behaviour: rolling and yesterday plots with all overlays,
# no 3/7-day plots.
PLOT_OPTION_DEFAULTS = {
    'rolling':   {'enabled': True,  'sun': True,  'xray': True,
                  'flares': True},
    'yesterday': {'enabled': True,  'sun': True,  'xray': True,
                  'flares': True},
    '3day':      {'enabled': False, 'sun': False, 'xray': True,
                  'flares': True},
    '7day':      {'enabled': False, 'sun': False, 'xray': True,
                  'flares': False},
}


def load_plot_options():
    """Return the per-plot-type options from plots.ini, with defaults.

    Returns {plot_type: {'enabled', 'sun', 'xray', 'flares'}} for the
    types rolling, yesterday, 3day and 7day. Missing files, sections,
    keys or unparseable values fall back to PLOT_OPTION_DEFAULTS.
    """
    parser = configparser.ConfigParser()
    parser.read(PLOTS_FILE)
    options = {}
    for section, defaults in PLOT_OPTION_DEFAULTS.items():
        values = {}
        for key, fallback in defaults.items():
            try:
                values[key] = parser.getboolean(section, key,
                                                fallback=fallback)
            except ValueError:
                values[key] = fallback
        options[section] = values
    return options


def write_plot_manifest(temp_path, stations):
    """Write <temp>/plots.json describing the plot files for the web page.

    The intranet page (WWW/index.html) fetches this manifest to discover
    which station plots exist and when they were last refreshed. Written
    atomically so the browser never reads a half-written file.

    Filenames are relative to the temp folder, which is organised into
    subfolders (the plot type is given by the folder, not the filename):
        rolling/day|3day|7day/<frequency_hz>.png   (rolling plots)
        periods/yesterday|3day|7day/<frequency_hz>.png
                                                   (midnight-aligned plots)
    The fallback entry names the X-ray only plots (NOAA.png in the same
    folders) used while no stations are configured. The periods entry
    tells the page which multi-day plots are enabled in plots.ini.
    """
    options = load_plot_options()

    def entries(name):
        # Forward slashes: these are URL/FTP paths relative to temp
        return {
            'rolling': f'rolling/day/{name}',
            'yesterday': f'periods/yesterday/{name}',
            '3day': f'rolling/3day/{name}',
            '7day': f'rolling/7day/{name}',
            'period3day': f'periods/3day/{name}',
            'period7day': f'periods/7day/{name}',
        }

    manifest = {
        'generated_utc': f'{utc_now():{TIME_FORMAT}}',
        'periods': {
            '3day': options['3day']['enabled'],
            '7day': options['7day']['enabled'],
        },
        'stations': [
            {
                'callsign': station['callsign'],
                'frequency_hz': station['frequency_hz'],
                **entries(f'{station["frequency_hz"]}.png'),
            }
            for station in stations
        ],
        'fallback': entries('NOAA.png'),
    }
    os.makedirs(temp_path, exist_ok=True)
    manifest_path = os.path.join(temp_path, 'plots.json')
    temp_file = manifest_path + '.tmp'
    with open(temp_file, 'w') as output:
        json.dump(manifest, output, indent=2)
        output.write('\n')
    os.replace(temp_file, manifest_path)


def plot_archive_path(plots_path, station_folder, plot_type, day, stem):
    """Date-stamped archive path for a plot, creating the folders:
        <plots>/<station_folder>/<plot_type>/YYYY/YYYY-MM/<stem>-YYYY-MM-DD.png

    station_folder is the callsign (or 'NOAA' for the fallback plots);
    plot_type is day, 3day or 7day; stem is the frequency in Hz (or 'NOAA').
    """
    folder = os.path.join(plots_path, station_folder, plot_type,
                          f'{day:%Y}', f'{day:%Y-%m}')
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f'{stem}-{day:%Y-%m-%d}.png')


def read_sun_times(data_path, day):
    """Sunrise and sunset timestamp strings from the daily sun file written
    by GetDataSun.py, or (None, None)."""
    path = os.path.join(data_path, 'Sun', f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')
    if not os.path.isfile(path):
        return None, None
    with open(path) as sun_file:
        fields = sun_file.readline().strip().split(',')
    if len(fields) >= 4 and fields[1] == 'sunrise' and fields[3] == 'sunset':
        return fields[0], fields[2]
    return None, None


def off_air_window(text, day):
    """Parse an "HH:MM-HH:MM" off-air window for the given date into
    (start, end, midpoint) timestamp strings, or None."""
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


def fetch_json(url, logfiles_path, source_name):
    """Fetch and decode a JSON file from a web service, retrying on failure.

    Raises RuntimeError once all attempts have failed; the caller should
    report this to logerror.log.
    """
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            response = requests.get(url, headers={'User-Agent': USER_AGENT},
                                    timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            last_error = error
            if attempt < RETRIES:
                log_message(logfiles_path, source_name,
                            f'Attempt {attempt} of {RETRIES} failed '
                            f'({error}) - retrying in {RETRY_DELAY}s')
                time.sleep(RETRY_DELAY)
    raise RuntimeError(
        f'Request failed after {RETRIES} attempts: {url} : {last_error}')
