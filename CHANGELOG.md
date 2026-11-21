# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses calendar versioning in the format `YYYY.MM.patch`.

## [Unreleased]

### Added

- `scripts/GetDataAerial.py`: VLF aerial data capture from the ABElectronics
  ADC Pi - a measurement cycle every 10 seconds (:00, :10, :20 ... of each
  minute) on every channel configured in `aerials.ini`, taking a trimmed
  mean of the configured samples and appending
  `timestamp,voltage,callsign` records to
  `data/Aerial/<CALLSIGN>/YYYY/YYYY-MM/YYYY-MM-DD.csv`. Failed reads are
  recorded as `nan` so plots show a gap. Hourly summaries go to
  `logfile.log`.
- `install/ukraa-vlf-aerial.service`: systemd unit running the aerial
  capture as an auto-restarting service.

### Changed

- `GetDataSun.py`: now runs hourly from cron and exits immediately if the
  day's sun file already exists, so a network outage at midnight (which
  previously lost the whole day's sunrise/sunset annotations) is retried
  every hour. New `--date YYYY-MM-DD` option to backfill a missed day and
  `--force` to re-fetch an already stored day.
- `aerials.ini.example` / `vlf_common.load_aerials()`: new `mode` key for the
  MCP3424 conversion mode (0 = one-shot, 1 = continuous); example now uses
  addresses 0x6E/0x6F, 12-bit resolution, 24 samples with trim 8.
- `install/crontabVLF.cron`: removed the legacy aerial watchdog entry - the
  capture now runs under systemd.

