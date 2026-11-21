#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# Program to record VLF receiver output voltages using the ABElectronics
# ADC Pi board (two MCP3424 chips, 8 single-ended channels, 0-5.06 V).
#
# All hardware settings come from config/aerials.ini (see
# install/aerials.ini.example): I2C chip addresses, bit resolution,
# conversion mode (one-shot/continuous), PGA gain, readings per measurement
# cycle (samples) and how many readings to discard from each end of the
# sorted set before averaging (trim).
#
# Intended to be run as a systemd service (see
# install/ukraa-vlf-aerial.service). The service uses Type=notify with a
# 60s watchdog: the script pings systemd every cycle, so a hung loop (e.g.
# a read blocked on a wedged I2C bus) is killed and restarted by systemd.
# If every channel fails for STALL_RESTART_CYCLES consecutive cycles the
# script exits so systemd restarts it, re-initialising the ADC hardware.
# Each measurement cycle:
#
#   1. Waits for the next 10-second boundary (:00, :10, :20 ... of each
#      minute), giving 6 measurement cycles per minute.
#   2. For every channel in aerials.ini with BOTH callsign and frequency_hz
#      set: takes <samples> readings, sorts them, discards <trim> readings
#      from the top AND the bottom, and averages the remainder.
#   3. Appends one record per channel to that station's daily file:
#        <data>/Aerial/<CALLSIGN>/YYYY/YYYY-MM/YYYY-MM-DD.csv
#      Folders are created as needed when the date changes.
#
# Data file record format (timestamp is the actual UTC read time):
#   yyyy-mm-dd hh:mm:ss,voltage(x.xxx),callsign
#
# If a channel read fails the value is written as "nan" (gnuplot treats NaN
# as missing data, so plots show a gap instead of breaking) and the failure
# is reported to logerror.log.
#
# Recording continues through any configured off_air window - the window is
# a plot annotation only.
#
# All timestamps (data, log entries) are UTC.
#
# Start-up, shutdown and hourly summaries are logged to logfiles/logfile.log;
# failures (library missing, bad configuration, ADC read errors, etc.) are
# logged to logfiles/logerror.log.
#
# Requires the ABElectronics ADCPi Python library:
#   https://www.abelectronics.co.uk/kb/article/1/adc-pi-raspberry-pi-analogue-to-digital-converter
# and I2C enabled on the Pi (sudo raspi-config -> Interface Options -> I2C).
#
# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

import os
import signal
import socket
import sys
import time

from vlf_common import load_aerials, load_paths, log_error, log_message, utc_now

SOURCE = 'GetDataAerial.py'

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
CYCLE_SECONDS = 10          # measurement cycle every 10 seconds (:00, :10, ...)

# If EVERY channel fails for this many consecutive cycles the ADC is assumed
# stalled: the service exits so systemd restarts it, re-initialising the
# I2C bus and ADC from scratch (30 cycles = 5 minutes)
STALL_RESTART_CYCLES = 30


# ==========================================================================================
#
# systemd integration
#
# ==========================================================================================

def sd_notify(message):
    """Send a state notification to the systemd notify socket.

    Used for Type=notify readiness (READY=1) and the WatchdogSec keep-alive
    (WATCHDOG=1). A silent no-op when not running under systemd (e.g. run
    by hand for testing).
    """
    socket_path = os.environ.get('NOTIFY_SOCKET')
    if not socket_path:
        return
    if socket_path.startswith('@'):     # abstract socket namespace
        socket_path = '\0' + socket_path[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(socket_path)
            sock.sendall(message.encode())
    except (OSError, AttributeError):
        pass


# ==========================================================================================
#
# Data file helpers
#
# ==========================================================================================

def day_file_path(data_path, callsign, day):
    """Path of a station's daily file:
    <data>/Aerial/<CALLSIGN>/YYYY/YYYY-MM/YYYY-MM-DD.csv"""
    return os.path.join(data_path, 'Aerial', callsign, f'{day:%Y}',
                        f'{day:%Y-%m}', f'{day:%Y-%m-%d}.csv')


def append_record(data_path, callsign, when, value):
    """Append one "timestamp,voltage,callsign" record to the station's
    daily file, creating folders as needed."""
    path = day_file_path(data_path, callsign, when.date())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as data_file:
        data_file.write(f'{when:{TIME_FORMAT}},{value:.3f},{callsign}\n')


# ==========================================================================================
#
# ADC measurement
#
# ==========================================================================================

def open_adc(adc_settings, logfiles_path):
    """Initialise the ADC Pi from the [MCP3424] settings, or None on failure."""
    try:
        from ADCPi import ADCPi
    except ImportError as error:
        log_error(logfiles_path, SOURCE,
                  f'ABElectronics ADCPi library not installed ({error}) - '
                  'see https://www.abelectronics.co.uk/kb/article/1/'
                  'adc-pi-raspberry-pi-analogue-to-digital-converter')
        return None
    try:
        address_1 = int(adc_settings['address_1'], 16)
        address_2 = int(adc_settings['address_2'], 16)
    except ValueError:
        log_error(logfiles_path, SOURCE,
                  f'Bad I2C address in aerials.ini [MCP3424]: '
                  f'address_1={adc_settings["address_1"]} '
                  f'address_2={adc_settings["address_2"]}')
        return None
    try:
        adc = ADCPi(address_1, address_2, adc_settings['resolution'])
        adc.set_pga(adc_settings['gain'])
        adc.set_conversion_mode(adc_settings['mode'])
    except (IOError, OSError, ValueError) as error:
        log_error(logfiles_path, SOURCE,
                  f'Failed to initialise ADC Pi at '
                  f'{adc_settings["address_1"]}/{adc_settings["address_2"]}: '
                  f'{error}')
        return None
    return adc


def measure_channel(adc, channel, samples, trim):
    """Trimmed mean of <samples> readings from an ADC channel.

    The readings are sorted and <trim> readings are discarded from each end
    before averaging. Raises on an ADC read failure.
    """
    readings = sorted(adc.read_voltage(channel) for _ in range(samples))
    kept = readings[trim:len(readings) - trim]
    return sum(kept) / len(kept)


def sleep_to_next_cycle():
    """Sleep until the next CYCLE_SECONDS boundary (:00, :10, :20, ...)."""
    time.sleep(CYCLE_SECONDS - (time.time() % CYCLE_SECONDS))


# ==========================================================================================
#
# Main capture loop
#
# ==========================================================================================

def run_capture(adc, stations, adc_settings, data_path, logfiles_path):
    """Measurement loop: one cycle every CYCLE_SECONDS, hourly summaries.

    Pings the systemd watchdog every cycle. Returns 1 if every channel has
    failed for STALL_RESTART_CYCLES consecutive cycles (stalled ADC - exit
    so systemd restarts the service and re-initialises the hardware).
    Otherwise runs until the process receives SIGTERM/SIGINT (systemd stop).
    """
    samples = adc_settings['samples']
    trim = adc_settings['trim']

    summary_hour = utc_now().hour
    cycles = 0
    failures = {station['callsign']: 0 for station in stations}
    stalled_cycles = 0

    while True:
        sleep_to_next_cycle()
        sd_notify('WATCHDOG=1')

        failed_this_cycle = 0
        for station in stations:
            when = utc_now()
            try:
                value = measure_channel(adc, station['channel'],
                                        samples, trim)
            except (IOError, OSError, ValueError) as error:
                value = float('nan')
                failures[station['callsign']] += 1
                failed_this_cycle += 1
                log_error(logfiles_path, SOURCE,
                          f'ADC read failed on channel {station["channel"]} '
                          f'({station["callsign"]}): {error}')
            append_record(data_path, station['callsign'], when, value)
        cycles += 1

        # Stalled ADC? (every channel failing) - exit so systemd restarts
        # the service and the ADC/I2C bus is re-initialised from scratch
        stalled_cycles = (stalled_cycles + 1
                          if failed_this_cycle == len(stations) else 0)
        if stalled_cycles >= STALL_RESTART_CYCLES:
            log_error(logfiles_path, SOURCE,
                      f'ADC stalled - all channels failed for '
                      f'{STALL_RESTART_CYCLES} consecutive cycles '
                      f'({STALL_RESTART_CYCLES * CYCLE_SECONDS // 60} '
                      f'minutes) - exiting for systemd to restart')
            log_message(logfiles_path, SOURCE,
                        'Abandoned VLF aerial data capture - '
                        'ADC stalled (see logerror.log)')
            return 1

        # Hourly summary to logfile.log
        hour = utc_now().hour
        if hour != summary_hour:
            failed = ', '.join(f'{callsign}: {count} failed'
                               for callsign, count in failures.items()
                               if count)
            log_message(logfiles_path, SOURCE,
                        f'Hourly summary: {cycles} measurement cycles'
                        f'{" (" + failed + ")" if failed else ""}')
            summary_hour = hour
            cycles = 0
            failures = {callsign: 0 for callsign in failures}


def main():
    paths = load_paths()
    logfiles_path = paths['logfiles']
    data_path = paths['data']

    log_message(logfiles_path, SOURCE, 'Started VLF aerial data capture')

    aerials = load_aerials()
    adc_settings = aerials['adc']
    stations = aerials['stations']

    if not stations:
        log_error(logfiles_path, SOURCE,
                  'No aerials configured in aerials.ini - set callsign and '
                  'frequency_hz for at least one channel')
        log_message(logfiles_path, SOURCE,
                    'Abandoned VLF aerial data capture - '
                    'no aerials configured (see logerror.log)')
        return 1

    if adc_settings['samples'] <= 2 * adc_settings['trim']:
        log_error(logfiles_path, SOURCE,
                  f'Bad [MCP3424] settings in aerials.ini: samples '
                  f'({adc_settings["samples"]}) must be greater than '
                  f'2 x trim ({adc_settings["trim"]})')
        log_message(logfiles_path, SOURCE,
                    'Abandoned VLF aerial data capture - '
                    'bad configuration (see logerror.log)')
        return 1

    adc = open_adc(adc_settings, logfiles_path)
    if adc is None:
        log_message(logfiles_path, SOURCE,
                    'Abandoned VLF aerial data capture - '
                    'ADC unavailable (see logerror.log)')
        return 1

    station_list = ', '.join(
        f'channel {station["channel"]} = {station["callsign"]} '
        f'({station["frequency_hz"]} Hz)' for station in stations)
    log_message(logfiles_path, SOURCE,
                f'Capturing every {CYCLE_SECONDS}s at '
                f'{adc_settings["resolution"]}-bit, gain '
                f'{adc_settings["gain"]}, '
                f'{"continuous" if adc_settings["mode"] == 1 else "one-shot"} '
                f'mode, {adc_settings["samples"]} samples trimmed by '
                f'{adc_settings["trim"]}: {station_list}')

    sd_notify('READY=1')     # Type=notify: tell systemd start-up succeeded

    # Let systemd stop the service cleanly (SIGTERM) or Ctrl-C when run by
    # hand (SIGINT) - both raise KeyboardInterrupt handled below
    def request_stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, request_stop)

    try:
        return run_capture(adc, stations, adc_settings, data_path,
                           logfiles_path)
    except KeyboardInterrupt:
        log_message(logfiles_path, SOURCE, 'Stopped VLF aerial data capture')
        return 0
    except Exception as error:       # noqa: BLE001 - log then let systemd restart
        log_error(logfiles_path, SOURCE,
                  f'Unexpected failure in capture loop: {error}')
        log_message(logfiles_path, SOURCE,
                    'Abandoned VLF aerial data capture - '
                    'unexpected failure (see logerror.log)')
        return 1


if __name__ == '__main__':
    sys.exit(main())
