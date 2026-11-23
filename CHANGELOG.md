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
- `scripts/CheckDataAerial.py` + cron entry: independent 10-minute check
  that aerial data is still arriving and not all-nan; alerts to
  `logerror.log` only (recovery is handled by systemd).
- `GetDataAerial.py` / `ukraa-vlf-aerial.service`: systemd `Type=notify`
  with a 60s watchdog (hung capture loop is killed and restarted) and a
  stalled-ADC self-restart - if every channel fails for 30 consecutive
  cycles (5 minutes) the service exits so systemd re-initialises the ADC.
- `WWW/index.html`: intranet page now displays the rolling 24-hour and
  yesterday plots. It reads a `plots.json` manifest from the temp folder
  (written by the plot scripts) to build one plot card per configured
  station - falling back to the NOAA X-ray only plots while no stations
  are configured - and shows a freshness banner that turns stale when the
  manifest is more than 15 minutes old. Magnetometer carry-over content
  (nT alert banner, HDZ/BI/period plots) removed.
- `vlf_common.write_plot_manifest()`: writes `<temp>/plots.json`
  (atomically) describing the stations and plot filenames; called from
  `PlotDataRolling.py` (every 5 minutes, keeps the freshness timestamp
  current) and `PlotDataYesterday.py`.
- `install/install_webserver.sh`: web server install section for the
  future `install.sh` - installs apache2 only (no PHP or database is
  needed), publishes `WWW/` to `/var/www/html` and points the `temp`
  path in `config/vlf.ini` at `/var/www/html/temp/` so the plot scripts
  write straight into the served folder.
- Data credits: `PlotRolling.gp` / `PlotYesterday.gp` now print
  "Data: NOAA SWPC | sunrise-sunset.org" in the bottom-right corner of
  every plot (each part only when that data is shown), and
  `WWW/index.html` links to NOAA SWPC and sunrise-sunset.org below the
  graphs - sunrise-sunset.org attribution is required by that API's
  terms of use; the NOAA credit is a courtesy (US Government data is
  public domain).
- `scripts/EvaluateAlerts.py` + `install/alerts.ini.example` + cron entry:
  email alerts, configured in `config/alerts.ini`. An alert email is sent
  when a GOES X-ray flare reaches the configured `flare_threshold`
  (e.g. C1.0 / M1.0 / X1.0), with a follow-up if NOAA later upgrades the
  flare to a higher class letter; state in `data/alerts/alert-state.json`
  ensures one email per flare per class letter and retries failed sends.
  A daily heartbeat email (at/after a configured UTC hour, default 09:00)
  summarises the last 24 hours of flares and whether the rolling plots
  are fresh. The current rolling plot(s) (one per configured station) can
  optionally be attached to either email. `--test-email` and
  `--test-heartbeat` options verify the SMTP settings.

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

