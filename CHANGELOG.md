# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses calendar versioning in the format `YYYY.MM.patch`.

## [Unreleased]

### Added

- `install/install.sh`: unattended installer (no questions asked) modelled
  on the magnetometer one. Run with
  `sudo bash ~/UKRAA_VLF/install/install.sh`; installs all dependencies
  (gnuplot, python3-requests, i2c-tools, python3-smbus2/smbus), enables
  the I2C interface and sets the system timezone to UTC, creates the
  directory structure and log files, copies the desktop wallpaper to
  `~/Pictures`, sets up all `config/*.ini` files
  from the examples (kept on re-run/upgrade), detects the MCP3424 ADC
  chips on the I2C bus (0x68-0x6F) and writes their addresses into
  `config/aerials.ini`, installs and starts the aerial capture service,
  installs the cron entries into the owner's crontab and installs the
  web server: apache2 only (no PHP or database is needed), publishing
  `WWW/` to `/var/www/html` and pointing the `temp` path in
  `config/vlf.ini` at `/var/www/html/temp/` so the plot scripts write
  straight into the served folder. The installation account is the
  account that
  invoked `sudo` (override with `VLF_FILE_OWNER`) - the username does not
  have to be `pi` - and all paths are taken from wherever the checkout
  lives.
- `scripts/ADCPi.py`: vendored copy of the ABElectronics ADC Pi library
  (MIT licence,
  https://github.com/abelectronicsuk/ABElectronics_Python_Libraries),
  so only its `smbus2` (or legacy `smbus`) dependency needs installing -
  no separate download of the AB Electronics repository is required.

### Changed

- `scripts/vlf_common.py`: the default base path is now the parent of the
  `scripts/` folder (instead of the hard-coded `/home/pi/UKRAA-VLF/`), so
  the software works unchanged from any installation directory and user
  account; `VLF_CONFIG` still overrides the config file location.

- `scripts/UploadDataWWW.py` + `install/remote-upload.ini.example` + cron
  entries: remote FTP upload of the plot images and the `plots.json`
  manifest to an external web site, configured in
  `config/remote-upload.ini`. The remote layout mirrors the local temp
  folder (`<directory>/temp/...`), so the same `WWW/index.html` works
  unchanged on the remote site (upload `index.html` and `WWW/images`
  there once, manually). Two modes run from cron shortly after the
  matching plot jobs: `rolling` (`--days 1/3/7` - every 5 minutes for
  the 24-hour plots, hourly for the 3/7-day plots) and `periods`
  (midnight-aligned plots, daily); `plots.json` is uploaded last so it
  never references an image that is not there yet. Plain FTP or explicit
  FTPS (`tls = true`) - for hosts without SFTP. While `enabled = false`
  (or the config file is absent) the script exits quietly, so the cron
  entries can stay in place.
- `scripts/PlotDataPeriod.py` + cron entries: static (midnight-aligned)
  3-day and 7-day plots covering complete UTC days, produced daily after
  the yesterday plots when the matching `3day`/`7day` section is enabled
  in `config/plots.ini` (the same sections that control the rolling
  multi-day plots). Shown on the web page alongside the rolling plots
  ("(rolling)" / "(complete days)").
- New `plots` entry in the `[paths]` section of `config/vlf.ini`
  (default `<home>/plots/`): a date-structured plot archive
  `plots/<CALLSIGN>/<type>/YYYY/YYYY-MM/<frequency_hz>-YYYY-MM-DD.png`
  where `<type>` is `day` (yesterday plots), `3day` or `7day` (static
  period plots); the X-ray only fallback plots archive under
  `plots/NOAA/` as `NOAA-YYYY-MM-DD.png`. Rolling plots are snapshots
  and are not archived.
- `scripts/vlf_plot.py`: shared plotting helpers (data-file locations,
  sun/night overlay assignments, gnuplot runner) used by
  `PlotDataRolling.py`, `PlotDataPeriod.py` and `PlotDataYesterday.py`.
- `scripts/MigratePlotsArchive.py`: one-off migration (with `--dry-run`)
  that moves the old `<data>/Plots/` archive files into the new
  `plots/` tree and deletes the old flat-layout PNGs from the temp
  folder.
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
- Web server install section (now part of `install/install.sh`) -
  installs apache2 only (no PHP or database is
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
- Optional rolling 3-day and 7-day plots (NOAA GOES style, 960x540,
  refreshed hourly from cron): `PlotDataRolling.py --days 3` / `--days 7`
  write `VLF3day<hz>.png` / `VLF7day<hz>.png` and appear automatically in
  a new "LONG PERIOD VLF RESULTS" section of the web page when enabled.
- `install/plots.ini.example` / `vlf_common.load_plot_options()`: new
  `config/plots.ini` controls which plots are produced (rolling,
  yesterday, 3day, 7day) and which overlays appear on each (sun shading,
  X-ray flux, flare markers), so busy multi-day plots can be decluttered.
  Defaults preserve the original behaviour. The transmitter off-air
  annotation is only drawn on the rolling and yesterday plots.
- `PlotRolling.gp`: generalised - parametrised canvas size, x-tic
  interval/format, up to 16 data files per trace and optional compact
  night shading (no text labels) for the multi-day plots.

### Changed

- The temp folder (served by Apache and, in future, uploaded by FTP) is
  now organised into subfolders where the folder names the plot type and
  the filename is the station frequency in Hz (`NOAA.png` for the X-ray
  only fallback):
  `rolling/day|3day|7day/<frequency_hz>.png` and
  `periods/yesterday|3day|7day/<frequency_hz>.png`. The `plots.json`
  manifest now carries these folder-relative paths (plus new
  `period3day`/`period7day` entries), and `WWW/index.html` and the
  `EvaluateAlerts.py` email attachments follow the manifest layout. The
  yesterday-plot archive moved from `<data>/Plots/` to the new `plots/`
  tree (run `MigratePlotsArchive.py` once on existing installations).
- All plots are now 960x540 (previously the rolling and yesterday plots
  were 640x540), so every graph on the web page is the same width; the
  page's graph frames widened to match.
- `WWW/images`: `UKRAA_VLF.png` (25.7 MB) and `header.png` (2.4 MB)
  replaced with web-sized JPEGs `UKRAA_VLF.jpg` (0.5 MB) and
  `header.jpg` (0.35 MB) - the originals were photographs served at full
  camera resolution on every page load.
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

