# UKRAA VLF data-wrangling report

**Review date:** 2026-10-15  
**Requirements addendum:** 2026-11-17  
**Scope:** The VLF acquisition, NOAA/Sun ingestion, event-extraction and plotting scripts present in this workspace, plus requirements and a proposed design for a downloadable Raspberry Pi Zero 2 W deployment.

## Executive summary

The VLF pipeline is a small, file-based ETL system. It records receiver voltages as timestamped daily text files, downloads daily space-weather and solar data, then joins those sources by timestamp to make day and event plots. Its strongest qualities are operational simplicity, readable output files and a clear separation between continuous receiver logging and scheduled batch jobs.

The most important concern is provenance: the VLF scripts examined here are under `examples/scripts`, and the repository's [.gitignore](../.gitignore) excludes the whole `examples/` directory. The tracked root [README.md](../README.md) identifies the PicoMagnetometer suite, not this VLF pipeline. The report therefore describes the VLF snapshot available in this workspace; it should not be treated as a review of a currently tracked, reproducible VLF release until that source is restored to the repository or its canonical location is confirmed.

Within that snapshot, the principal data risks are:

1. X-ray bands are paired using implicit API record order rather than a timestamp key. Missing or reordered records can silently associate a flux with the wrong minute.
2. Event-data paths use the current year but yesterday's month and day. On January 1, the batch processor looks in the wrong year for yesterday's data.
3. Derived daily/event outputs use append mode, so reruns duplicate data and can leave stale counts or plots.
4. Date calculations mix local system time with UTC observation timestamps and GNUplot's host-local `date` command.
5. Network responses are consumed without explicit timeouts, status checks or validation of the expected payload shape.

The requirements addendum in sections 9-14 defines the intended new project: a Raspberry Pi Zero 2 W with an AB Electronics ADC Pi reading the receiver's 0-5 V output, user-configured transmitter metadata, daily and five-minute-refreshed rolling plots, and a locally hosted dashboard. Optional remote uploads and email alerts should follow the operational style of the supplied magnetometer examples. These are requirements and recommendations, not claims that the installation or features have already been implemented or hardware-tested.

## 1. Scope and evidence

The local VLF material reviewed includes:

- Receiver collectors: [GetDataAerial.py](../examples/scripts/GetDataAerial.py) and [GetDataAerial19600.py](../examples/scripts/GetDataAerial19600.py).
- NOAA ingestion: [GetDataNOAAsatellites.py](../examples/scripts/GetDataNOAAsatellites.py), [GetDataNOAAxrays.py](../examples/scripts/GetDataNOAAxrays.py) and [GetDataNOAAxray-flares.py](../examples/scripts/GetDataNOAAxray-flares.py).
- Solar times and date configuration: [GetDataSun.py](../examples/scripts/GetDataSun.py), [VLFcalender.py](../examples/scripts/VLFcalender.py) and [vlfdata.ini](../examples/data/vlfdata.ini).
- Event-window extraction and plotting: [CreateDataEventsPlotsDHO.py](../examples/scripts/CreateDataEventsPlotsDHO.py), [CreateDataEventsPlotsGQD.py](../examples/scripts/CreateDataEventsPlotsGQD.py), and the DHO/GQD GNUplot scripts.
- Example outputs under `examples/data`, including NOAA X-ray and flare daily files.

These files were read directly. The principal ingestion and event Python files were syntax-checked with `py_compile`; that check does not establish that the scripts run correctly against NOAA, the sunrise API, Raspberry Pi hardware or production data. The local `test/` directory contains no tests for these example scripts.

For comparison, this report inspected the tracked Python pipeline in [UKradioastro/UKRAA_Magnetometer](https://github.com/UKradioastro/UKRAA_Magnetometer), particularly `scripts/ProcessDataRaw.py`, `scripts/ProcessDataHour.py`, `scripts/ProcessDailySummary.py`, `scripts/space_weather.py`, `scripts/magnetometer_common.py` and its tests. It is a related UKRAA Raspberry Pi data-collection and presentation suite, but processes magnetometer measurements rather than VLF receiver voltage.

## 2. How the VLF data flow works

### 2.1 Receiver acquisition

`GetDataAerial.py` and `GetDataAerial19600.py` continuously read the ADC Pi using the ABElectronics `ADCPi` library. The first collector reads channel 1 and the second reads channel 5. They append one voltage value per cycle to a daily text file and sleep until the next minute boundary.

The directory layout is date-partitioned:

```text
data/Aerial/YYYY/YYYY-MM/YYYY-MM-DD.txt
data/Aerial19600/YYYY/YYYY-MM/YYYY-MM-DD.txt
```

Each record is a UTC timestamp and voltage, separated by a comma, for example:

```text
2026-01-01 00:00:00,1.2345
```

The collector's append-only approach is appropriate for a continuous stream: an individual measurement should not replace the day's previous measurements. The paths are nevertheless hard-coded under `/home/pi/VLF/data/`, rather than consistently derived from the configuration file.

### 2.2 NOAA and solar ingestion

`GetDataNOAAsatellites.py` fetches NOAA's instrument-source JSON and updates primary/secondary satellite numbers in `vlfdata.ini`. `GetDataNOAAxrays.py` fetches the three-day JSON feeds for both primary and secondary instruments, selects records for the configured previous day, and stores paired soft- and hard-band flux values. The daily row format shown in the example data has six fields:

```text
UTC timestamp, satellite, soft flux, soft energy band, hard flux, hard energy band
```

`GetDataNOAAxray-flares.py` fetches the seven-day flare feeds for primary and secondary instruments. It selects records whose `time_tag` falls on the previous day and writes each event's maximum time and flux, start and end times, class and satellite number.

`GetDataSun.py` calls the Sunrise-Sunset API for the configured London coordinates. It extracts UTC sunrise and sunset times and writes one dated record to each of the `SunRise` and `SunSet` trees. `VLFcalender.py` maintains `calender_today`, `calender_yesterday` and `calender_tomorrow` year/month/day strings in the INI file; the legacy spelling `calender` is part of the current config contract.

The NOAA and solar scripts are batch jobs, not live stream processors. Their output is also partitioned by year and month, with one daily file per source/day.

### 2.3 Event-window extraction

The DHO and GQD processors read the previous day's flare events, sunrise/sunset, X-ray data and receiver data. They use CSV readers with manually specified field names, parse timestamps into `datetime` values, and select events whose window from 30 minutes before event start to 30 minutes after event end lies wholly between sunrise and sunset.

For each qualifying event, the scripts write:

- a file containing the X-ray samples in the event window;
- a file containing the receiver samples in that window;
- an event metadata row with start, peak, end and class;
- a daily event-count file.

GNUplot reads those files and produces receiver/X-ray daily charts and event charts. The DHO daily plot uses the receiver voltage from column 2 and the hard X-ray flux from column 5 of the X-ray file, adds flare markers, and annotates sunrise/sunset. See [PlotDataYesterdayDHO.gp](../examples/scripts/PlotDataYesterdayDHO.gp) and [PlotExtractedDataYesterdayDHO.gp](../examples/scripts/PlotExtractedDataYesterdayDHO.gp); corresponding GQD scripts implement the other transmitter view.

### 2.4 Operations and data products

The design expects a Raspberry Pi, fixed installation paths, local configuration and scheduled jobs (the scripts contain example cron instructions). The continuous aerial collectors are separate from the daily retrieval, extraction and plotting steps. Outputs are plain text/CSV-like files, which are easy to inspect and consume with GNUplot, but have no explicit schema version or consistently enforced header.

## 3. Strengths

- **Simple operational model.** Plain files and cron jobs are understandable on a small Raspberry Pi and do not require a database service.
- **Human-readable archival layout.** Year/month/day partitioning makes it straightforward to inspect and copy a particular day's measurements.
- **The live receiver stream is append-only.** This preserves sequential measurements instead of overwriting prior samples.
- **UTC is recognized as the comparison time base.** The receiver collector timestamps in UTC, NOAA's `time_tag` is UTC, and the solar-times script requests unformatted UTC values.
- **Both X-ray bands and source satellite are represented in the example row format.** This is useful for plotting and later interpretation when the feed changes satellites.
- **The event view is scientifically motivated.** The processor narrows large daily files to an event-centered interval and excludes events whose chosen window extends outside daylight.
- **Daily and event plots are separate products.** This keeps the archival measurements distinct from the derived visualization inputs.

## 4. Weaknesses and design constraints

- **The VLF source is not part of the tracked project snapshot.** `examples/` is ignored, so changes to these scripts are not naturally reviewed, released or exercised by this checkout's tests.
- **Data contracts are implicit.** Column order, units, UTC semantics, missing-value conventions and source identity are mostly documented in comments or assumed by GNUplot.
- **Path/date logic is repeated.** Each script constructs its own year/month/day path, often with slightly different rules and direct string concatenation.
- **Batch transforms are not safely repeatable.** Append mode is used both for raw acquisition and for outputs that should be reproducible from source data.
- **External dependencies are loosely checked.** Scripts generally parse response text directly and assume the API returned the expected JSON keys and types.
- **File I/O and transformations are interleaved.** Large scripts contain path setup, download, parsing, filtering and output writing in one procedural flow, making unit-level verification difficult.
- **Coverage and quality are not first-class outputs.** The extractors do not report expected versus received samples, gaps, duplicate timestamps, or whether both X-ray channels were present.
- **Fixed installation assumptions reduce portability.** `/home/pi/VLF/...`, device addresses and transmitter timings are embedded in scripts, and configuration is not applied consistently.

## 5. Existing bugs and recommended fixes

The same DHO-specific issues apply to the GQD counterpart where indicated. Priority is about data correctness and operational impact, not security severity.

| Priority | Finding | Evidence and effect | Recommended correction |
|---|---|---|---|
| P1 | **X-ray channel pairing depends on feed order.** | In [GetDataNOAAxrays.py](../examples/scripts/GetDataNOAAxrays.py), the short-band values are assigned in the `0.05-0.4nm` branch and the row is written in the `0.1-0.8nm` branch (primary lines 336-390; secondary lines 571-625). The row uses the short-band timestamp and values together with the most recently seen long-band value. If a band is missing, the previous minute's value can be reused; if the first matching item is long-band, the short-band variables may not yet exist. | Parse into a map keyed by `(time_tag, satellite)`, with one value per energy band. Emit only complete pairs, or explicitly represent missing values; validate equal timestamps and source IDs before writing. Add fixtures for short-first, long-first, missing-band and out-of-order inputs. |
| P1 | **Yesterday's year path is wrong at New Year.** | In both [CreateDataEventsPlotsDHO.py](../examples/scripts/CreateDataEventsPlotsDHO.py) and [CreateDataEventsPlotsGQD.py](../examples/scripts/CreateDataEventsPlotsGQD.py), `GetPathnameYear()` uses the current year (line 95), while `GetPathnameYearMonth()` uses yesterday's month (lines 104-105) and the day filename also uses yesterday (lines 113-122). On January 1, the resulting path combines the new year with December and the previous day's date. Reads of yesterday's source files and writes of yesterday's event products therefore target the wrong tree. | Compute one `target_date = yesterday` once, then derive every path component from that same date. Add a December 31 / January 1 regression test for both sites. |
| P1 | **Batch and event outputs duplicate on rerun.** | NOAA daily rows are opened in append mode in [GetDataNOAAxrays.py](../examples/scripts/GetDataNOAAxrays.py) (lines 375 and 610); flare rows are appended in [GetDataNOAAxray-flares.py](../examples/scripts/GetDataNOAAxray-flares.py) (lines 380 and 616); solar times are appended in [GetDataSun.py](../examples/scripts/GetDataSun.py) (lines 481 and 602). Event VLF/X-ray/metadata files and `NumberOfEvents` are also opened with `a+` in the DHO and GQD processors (DHO lines 937, 977, 992 and 1022). A retry or manual re-run duplicates the same observations; the event-count file can contain multiple conflicting rows. | Keep append semantics for the live receiver log only. For fetched daily and derived products, build a complete temporary file and atomically replace the destination after successful validation. Make event extraction a pure, repeatable transform of input files. |
| P2 | **UTC and local-date calculations can disagree.** | The aerial collectors use UTC-aware datetimes ([GetDataAerial.py](../examples/scripts/GetDataAerial.py), lines 77-89 and 124), but `VLFcalender.py` derives all date strings from naive local `datetime.now()` (lines 27-72). The event processors also use naive local time to select yesterday, while GNUplot scripts derive yesterday using the host's `date` command. NOAA records and solar times are UTC. Around local/UTC midnight this can select different date partitions and omit or mislabel the UTC day's final/initial samples. | Select a single explicit timezone policy, preferably UTC for all stored filenames and timestamps, and pass an aware target date through every stage. If reports need a local observing day, convert at one documented boundary rather than mixing clocks. |
| P2 | **Network failures and invalid feeds are not handled robustly.** | NOAA scripts use `requests.get(..., stream=True)` and immediately parse `response.text` with `json.loads` (for example [GetDataNOAAxrays.py](../examples/scripts/GetDataNOAAxrays.py), lines 267-274 and 502-509). The NOAA and sunrise requests do not set a timeout or explicitly check HTTP status or response schema. A slow connection can stall a scheduled job; an HTTP error or changed payload surfaces as an opaque parse/key failure, while an unexpected but valid empty payload can complete without producing useful rows. | Use finite connect/read timeouts, `raise_for_status()`, bounded retry/backoff for transient failures, and explicit shape/type checks for required fields. Log endpoint, target date and failure context; do not create or replace the daily output on a failed fetch. |
| P3 | **Aerial timestamps are assembled from multiple clock reads.** | [GetDataAerial.py](../examples/scripts/GetDataAerial.py) formats the date and time using separate `datetime.now(timezone.utc)` calls (line 124), after independently deriving the destination path (lines 132-137). A boundary rollover between calls can place a record under one day while its timestamp says another. This is rare, but it complicates recovery and day-based processing. | Capture one `now_utc` per sample and use it for both the destination path and serialized timestamp. |
| P3 | **The code is hard to regression-test in its present repository state.** | The VLF scripts are ignored under `examples/`; the local `test/` directory has no corresponding tests. The tracked README describes a different application. This allows the source, docs and generated example data to drift independently. | Restore the canonical VLF scripts to a tracked source directory (or identify the intended upstream source), document their installation and add fixtures/tests before changing pipeline behavior. |

## 6. Comparison with UKRAA's PicoMagnetometer pipeline

The closest relevant comparison found in the UKRAA organization is [UKRAA_Magnetometer](https://github.com/UKradioastro/UKRAA_Magnetometer). Its data path is more deliberately staged:

1. `ProcessDataRaw.py` reads raw measurements through the shared `read_raw_rows` helper, buckets samples into 1,440 minute bins and writes a fixed daily minute series. Empty bins become `NaN` rather than disappearing, making gaps visible.
2. `ProcessDataHour.py` performs a separate hourly aggregation.
3. `ProcessDailySummary.py` produces a summary with valid-minute counts and coverage percentage, writes a temporary file and uses `os.replace()` so readers do not see a partially written summary.
4. `space_weather.py` has testable parsing/building functions and a fetch helper with timeouts, retry behavior, HTTP-error reporting and JSON validation.
5. The repository has focused tests for raw formats, daily summaries and space weather, among other installation and configuration tests.

That code is not a drop-in replacement for VLF: its sensor schema, calculations and aggregation windows differ. Its useful patterns for this suite are the shared path/date helpers, explicit parsing functions, explicit gap representation, atomic replacement of derived products, structured failure reporting and fixture-driven tests. The VLF code's append-only minute acquisition remains appropriate; it is the batch-derived outputs that should adopt replaceable, deterministic writes.

## 7. Suggested future direction

### Near term: make the VLF pipeline reproducible

1. Confirm which source is authoritative, then track it in a clearly named directory instead of the ignored `examples/` tree. Align the project README and installation instructions with the VLF deployment.
2. Add a small set of regression tests around the P1/P2 findings: paired NOAA bands, cross-year target dates, and rerunning a daily transform without changing its output.
3. Centralize date handling, path construction, directory creation and CSV schemas in a shared helper. Pass an explicit target date instead of recomputing `now()` in each stage.
4. Use `csv.reader`/`csv.writer` consistently with UTF-8 and explicit newline handling. Preserve field names, units, timezone and source identity in a schema document or CSV headers.

### Medium term: improve data integrity and operations

- Keep a raw copy or checksum/metadata for each downloaded API response, alongside retrieval time, endpoint and target date. This makes later reprocessing auditable.
- Validate each day's expected record coverage (nominally 1,440 minute samples for a continuously running receiver), duplicate timestamps and both X-ray bands. Record gaps as missing values rather than silently filling them from a previous sample.
- Write NOAA, solar and event-derived files to temporary paths, validate row counts and timestamps, then atomically replace the final file. A failed batch should leave the previous known-good output intact.
- Give each external source a small client with timeout, retry policy, response validation and clear logs. Keep API access out of the transformation functions so those functions can be tested offline.
- Add operational checks that distinguish "no event occurred" from "feed unavailable", "no receiver data" and "plot could not be built".

### Longer term: establish a maintainable data contract

Keep the existing human-readable files and GNUplot presentation while first standardizing their contract. If the number of sensors, derived products or consumers grows, consider a small SQLite index or a columnar store for querying, but retain immutable raw captures and stable exports so old plots and research workflows remain reproducible. Establish a reprocessing command that accepts an explicit date range and safely rebuilds all derived outputs.

## 8. Recommended order of work

1. **Resolve source provenance and tracking** so the reviewed code is part of the project being maintained.
2. **Fix X-ray pairing and the New Year's date path**; add tests before operational rollout.
3. **Make daily/event jobs idempotent** with validated temporary outputs and atomic replacement.
4. **Standardize UTC date handling and network failure policy.**
5. **Add coverage checks, schema documentation and routine regression tests.**

This sequence prioritizes corrupt or missing scientific data, then makes later refactoring safer without requiring a disruptive database or plotting rewrite.

## 9. Deployment requirements addendum

The following requirements were supplied after the original review. They extend the target project rather than changing the findings about the legacy VLF scripts.

| Area | Required outcome |
|---|---|
| Computer | Raspberry Pi Zero 2 W, with a suitable Raspberry Pi OS installation, network access and the required GPIO header fitted. |
| Analogue input | AB Electronics ADC Pi expansion board converting the UKRAA VLF receiver's 0 V to +5 V output into voltage measurements. |
| Transmitter identity | User-editable INI configuration identifying the monitored station and frequency. The initial installation is monitoring **DHO38 at 23.4 kHz (23400 Hz)**. |
| Archived plots | Daily VLF plots following the useful presentation in the supplied VLF examples, retaining NOAA context and event views where data are available. |
| Live plots | A genuine trailing **24-hour plot, regenerated and published every five minutes**, including across UTC midnight. |
| Distribution | All required application code, templates and web assets tracked in `UKradioastro/UKRAA_VLF`, so users can download or clone the project and run a single installer command. |
| Installation | A shell installer named `install.sh`, responsible for dependencies, configuration setup, acquisition service, scheduled processing and the local web server. |
| Logging | The timestamped, aligned source-and-message style supplied in the magnetometer examples, with operational and error logs. |
| Local viewing | A web page hosted on the Pi and accessible from browsers on the user's home intranet. |
| Optional publishing | Configurable FTP upload to the user's own website/hosting account, without making local operation dependent on that host. |
| Optional notifications | Configurable email alerts identifying significant candidate events for the observer to examine. |
| BAA report preparation | Reviewable SID start, peak, end and importance records, with a monthly report following the BAA VLF project's published table. Automatic submission is not assumed. |
| Implementation | Shell, Python and GNUplot are appropriate; adapt the supplied examples rather than transplanting magnetometer-specific scientific calculations. |

### 9.1 Additional local evidence

The newly supplied reference material is under `examples/example_install`, `examples/example_scripts` and `examples/example_WWW`:

- [install.sh](../examples/example_install/install.sh) demonstrates installation and configuration setup, but also installs Apache, PHP and MariaDB. A static VLF dashboard does not require the PHP/database stack; do not copy those dependencies without a specific need.
- [crontabMagnetometer.cron](../examples/example_install/crontabMagnetometer.cron) schedules rolling processing every five minutes and separates daily processing, housekeeping and health checks.
- [ProcessRolling.py](../examples/example_scripts/ProcessRolling.py) builds a trailing window from date-partitioned inputs and represents empty minute bins as missing values. Its vector-field calculations and geomagnetic activity levels are not applicable to VLF voltage.
- [processRollingData.sh](../examples/example_scripts/processRollingData.sh) demonstrates process/plot/alert/publish sequencing and keeping the local publication when remote upload fails.
- [logging.sh](../examples/example_scripts/logging.sh) and [runCronJob.sh](../examples/example_scripts/runCronJob.sh) provide aligned log records and timestamped stderr capture while preserving the job's exit status.
- [remote-upload.ini.example](../examples/example_install/remote-upload.ini.example) and [alerts.ini.example](../examples/example_install/alerts.ini.example) demonstrate opt-in publishing and SMTP configuration. Their placeholder credentials are not deployment settings, and their magnetic-field thresholds must not become VLF thresholds.
- [index.html](../examples/example_WWW/index.html) demonstrates daily/rolling presentation, status display and a 300,000 ms refresh interval. It uses external stylesheets/fonts; an intranet dashboard intended to work without internet access should serve its required assets locally.

These are design references read from the local workspace, not evidence that the final VLF release includes these facilities. As noted earlier, the `examples/` tree is ignored: production code must not depend on files left only in that tree.

## 10. Hardware, station metadata and acquisition

### 10.1 ADC Pi integration

The [manufacturer's ADC Pi page](https://www.abelectronics.co.uk/p/69/adc-pi), consulted on 2026-11-17, specifies eight single-ended inputs with a nominal input range of 0-5.06 V and lists Raspberry Pi Zero 2 W compatibility. This matches the receiver's stated 0-5 V output range. Wiring must follow the board documentation, with a shared signal ground and the receiver output connected to an ADC Pi analogue input, **not directly to a Raspberry Pi GPIO input**.

Use the manufacturer's `ADCPi` Python library and make the input channel, I2C bus, both chip addresses, conversion bit mode and gain explicit configuration. The existing [GetDataAerial.py](../examples/scripts/GetDataAerial.py) uses addresses `0x68` and `0x69`, channel 1, and library bit mode `12`; these are legacy settings, not a reason to hard-code the new deployment. Check the physical address jumpers and retain gain 1 for the full input range.

The manufacturer describes effective single-ended resolution as 11/13/15/17 bits, while the legacy library interface accepts converter bit modes 12/14/16/18. Document that distinction and verify the chosen library version and mode on the actual board. ADC conversion rate and the application's recording interval are separate settings.

The measured voltage is the tuned receiver's detected signal-level output. It is not a sampled 23.4 kHz waveform, does not directly measure the tuned frequency, and should not be labelled as calibrated radio field strength without a calibration model.

### 10.2 User-completed station configuration

An INI file is an appropriate way to identify the monitored transmitter. For example, the following is a **proposed configuration fragment**, not an existing file or finalized configuration contract:

```ini
[station]
callsign = DHO38
frequency_hz = 23400

[adc]
channel = 1
address_1 = 0x68
address_2 = 0x69
gain = 1
```

The user must physically tune the aerial/receiver and then enter the station/frequency to match. The software cannot establish that tuning from the DC voltage alone. Validate the configuration at startup, display `DHO38 - 23.4 kHz` on the web page and plots, and retain the metadata with the recorded observations.

Keep receiver/installation identity distinct from transmitter callsign. Record configuration changes with an effective UTC time or configuration identifier so retuning does not relabel historic measurements; split data streams or otherwise retain the station identity for each interval. Observer location, used for solar/path context and any future reports, should be separately configurable rather than inheriting the legacy London coordinates.

The [SID Station transmitter list](https://sidstation.loudet.org/stations-list-en.xhtml), consulted on 2026-11-17, lists DHO38 at 23400 Hz in Rhauderfehn, Germany. The page states **Last Update: 31 Jul 2023** and explicitly warns of obsolete or erroneous entries. Link to it as a reference, allow manual callsign/frequency entry, and do not require a live lookup or treat the list as proof that a transmitter is currently operating.

### 10.3 Acquisition contract

Run one lightweight collector under `systemd`, using the installation owner's unprivileged account with the necessary I2C permissions. Initialize the ADC once, capture a single UTC timestamp per observation, and append the measurement to the matching date partition. Preserve observations through midnight and service restarts.

The existing one-minute recording interval is a reasonable starting proposal, but is not yet a confirmed scientific requirement. Confirm the cadence against the desired event timing and any reporting requirements; higher-rate raw acquisition can be aggregated into minute plots without discarding the originals. Do not equate five-minute plot refresh with five-minute measurement sampling.

Retain timestamp, receiver/station identity, voltage units and quality/provenance metadata through a documented schema and associated configuration snapshots. I2C read failures must produce visible health errors, not invented zero readings. Missing, stale, out-of-range and near-rail/clipped data should be distinguishable from ordinary voltage variations.

## 11. Daily processing, rolling plots and intranet dashboard

### 11.1 Proposed processing model

Keep the file-based design and a small shared VLF helper module for configuration, UTC paths, parsing, logging and validated atomic writes:

```text
ADC Pi -> collector service -> append-only dated voltage records
                                   |
                +------------------+-------------------+
                |                                      |
         daily processing                     five-minute rolling job
                |                                      |
       daily/event CSV + plots             latest 24-hour CSV + plot + status
                |                                      |
                +------------> local static web page <--+
                                             |
                                  optional remote publication

Candidate-event evaluation -> optional email notification
NOAA/solar inputs          -> contextual overlays and event review
```

External downloads, rendering, email and remote hosting must not block acquisition. Internet loss should leave voltage recording and local voltage plots operational, with unavailable or stale contextual feeds clearly identified.

Daily plots should cover a full UTC day and retain a dated archive. Reprocessing an explicit date must replace derived products deterministically rather than append duplicates. Preserve familiar VLF/NOAA presentation, but show an absent overlay as unavailable rather than suppressing valid receiver data.

### 11.2 Exact rolling-window requirement

Every five minutes, choose one UTC end boundary, rounded down to the minute, and build the half-open interval `[end - 24 hours, end)`. Read whichever dated source files overlap that interval, including the previous month/year where necessary. A minute-binned output should contain **1,440 timestamped bins**, even when some contain no observation; encode gaps as missing values and never carry a previous voltage forward to conceal a gap.

Use GNUplot to render voltage against UTC time, with station/frequency, units, window bounds and generation time. If the receiver was retuned within the window, distinguish or separate the station intervals rather than joining them as one signal. Show coverage and newest-sample age in the accompanying status. At first startup the unobserved part of the window remains a gap, not an apparently measured zero.

Schedule the rolling job with a five-minute cron entry or equivalent timer, and use a lock to prevent overlapping runs. Read a consistent snapshot of completed acquisition records so an in-progress append cannot create a malformed final row. Build and validate CSV, status and image outputs before publication; use temporary files on the destination filesystem and atomic replacement. Publish a generation identifier or manifest last so the dashboard can detect mismatched assets.

The page should refresh the plot/status every five minutes without browser-cache staleness. Plot generation, local publication and browser refresh are distinct requirements: refreshing an old image alone does not satisfy the rolling requirement. Preserve the previous good plot after a processing failure, but label its age/staleness rather than presenting it as current.

### 11.3 Local web service

Use a lightweight static web-server configuration suitable for the Zero 2 W. The dashboard should provide:

- the rolling 24-hour plot, yesterday's daily plot and access to archived daily plots;
- station/frequency and receiver identity, with UTC labels;
- latest observation time, generation time, sample coverage and acquisition/processing health;
- a clear distinction between candidate events, no candidate events and insufficient data;
- downloadable observation data and candidate-event details where available.

Serve only published images, data and status, not the checkout, configuration secrets or operational logs. Keep required styling/scripts local and avoid exposing the Pi to the public internet as part of installation. Document access by hostname, for example `http://<pi-hostname>.local/`, and by its LAN IP address where `.local` resolution is unavailable.

## 12. Installation, logging and optional integrations

### 12.1 Single-command installation from the downloaded project

Provide a tracked root installer so, after downloading/unpacking or cloning the repository and changing into its directory, the user runs:

```sh
sudo bash ./install.sh
```

This is the proposed installation interface, not a command that the current checkout has been verified to support. Preparing the OS, Wi-Fi, physical hardware and obtaining the repository are prerequisites; the installer must not claim to perform physical tuning.

The installer should:

1. Check the supported Raspberry Pi OS/Python environment and identify the invoking non-root account without assuming its name is `pi`.
2. Install only required packages: Python support, the chosen ADC library and I2C tools, headless GNUplot, a static web server and the scheduling/locking tools actually used. Use an application virtual environment for non-OS Python dependencies where appropriate.
3. Enable/check I2C and account permissions, explicitly reporting any required reboot or missing hardware. Check both configured chip addresses and a real voltage read before declaring acquisition healthy.
4. Create owned data, configuration, temporary, published-web and log directories; generate user-editable INI files from tracked templates.
5. Install/enable the collector service and scheduled daily, rolling and log-maintenance jobs without duplicating entries.
6. Publish the initial dashboard with an honest waiting-for-data state and print the local URL and configuration locations.
7. Preserve user configuration and raw data on repeat installation/update; validate configuration changes rather than silently resetting them.

All runtime code and assets must work from a clean GitHub checkout with no ignored example files. Document configuration, wiring, OS support, updating, troubleshooting and recovery. Hardware/OS support should be described as tested only after validation on the intended Zero 2 W.

### 12.2 Logging and health

Reuse the example logging style with a VLF-specific main filename, for example `log-VLF.txt`, and a separate `log-error.txt`:

```text
2026-11-17 11:15:00 : processRollingData.sh       : Started rolling processing and publishing
2026-11-17 11:15:02 : processRollingData.sh       : Completed rolling plot and local publication
```

Use UTC consistently and document that log timestamps are UTC; the original shell formatter uses the host timezone unless explicitly configured otherwise. Apply the same format to Python and shell messages. Include job start/completion/failure, target date/window, coverage and actionable error context, and capture stderr without losing the originating exit status. Never log passwords.

Rotate/compress logs to avoid filling the SD card. Track acquisition freshness separately from plot/publication health: a stopped collector must not be hidden by a recently regenerated image. Check clock synchronization before treating timestamps as scientifically reliable, particularly after a reboot without network time.

### 12.3 Optional FTP publication

Adapt the remote-upload INI pattern, disabled by default, for the user's own hosting account. Keep credentials outside version control and outside the served web directory with restricted permissions. Upload only an explicit set of public plots/data/status assets; use finite timeouts, bounded retries and a logged outcome. Prefer staged upload/rename where the host supports it.

Retain FTP compatibility if required by the host, but explain that plain FTP exposes credentials and data in transit. Prefer FTPS or SFTP when available; these need protocol-specific configuration and must not be confused with ordinary FTP. Remote failures must preserve successful local publication and must not interrupt collection.

### 12.4 Optional significant-event email

Adapt the SMTP configuration, test-email facility and persistent notification-state pattern from the examples, disabled until configured. Use encrypted SMTP transport, finite timeouts and explicit delivery-failure logs. Deduplicate alerts across runs/restarts and apply cooldown/hysteresis so one event does not generate an email every five minutes.

Define a VLF-specific candidate-event method before enabling unattended alerts. A starting design could measure sustained positive **or negative** departures from a suitable daylight baseline, subject to configurable duration, data-quality and freshness checks. Thresholds require validation against representative observations; neither raw voltage thresholds alone nor the magnetometer's nT/AuroraWatch levels establish a SID.

Distinguish sunrise/sunset transitions, transmitter shutdowns, interference, retuning and ADC clipping from plausible ionospheric disturbances. NOAA X-ray timing is useful corroboration, not proof; a feed outage must be distinguished from absence of a flare. Candidate emails should include station/frequency, UTC interval, measured departure, quality/context and a plot or dashboard link, explicitly requesting human review rather than asserting a confirmed SID.

## 13. British Astronomical Association SID reporting

The user supplied the official [BAA Radio Astronomy Section VLF Project guidance](https://britastro.org/section_information_/radio-astronomy-section-overview/current-projects-observations/vlf-project), consulted on 2026-11-17. This provides a concrete basis for report preparation:

| Published field | Proposed handling |
|---|---|
| Date | The observation date in UT, with an unambiguous date in the stored record. |
| Start | Receiver-observed SID onset, proposed by detection and confirmed or corrected by the observer. |
| Peak | Time of the SID's maximum disturbance, including inverted events; allow observer selection for complex or multiple peaks. |
| End | Recovery/end time where measurable. Permit an unknown value rather than inventing a recovery time. |
| Importance | An observer-reviewed classification. Store as a text value so ratings such as `2+` are preserved. |

The page states that all times are **Universal Time (= GMT)** and requests monthly observations by the **15th of the succeeding month**, sent to the named project contact on that page. It does not publish a machine-readable upload schema or submission API. Prepare an export and readable monthly table for the user to check and submit through the published route; do not assume automatic submission is supported or authorized.

The BAA examples explicitly include inverted, double-peaked, sunset-confounded and overlapping SIDs. They explain that some end times cannot be measured and should be left blank; the example table represents those as `?` and the associated unassigned importance as a dash. Preserve unknowns internally and render them clearly in the report. Never replace a missing end time with the end of the extraction window or the NOAA flare's end time.

The examples include importance values `2+` and `3`, but **this page does not define the importance scale or its calculation**. Confirm that classification with the BAA project coordinator or an authoritative reporting guide before automating it. Do not equate importance with peak ADC voltage, NOAA GOES flare class, notification severity or an assumed duration formula. Until the rule is verified, provide a manually editable field and explicitly flag unassigned ratings for review.

Candidate extraction should therefore produce a review record containing estimated start/peak/end, event polarity, quality flags and a supporting plot, alongside separate observer-approved values and notes. BAA timings describe the disturbance in the receiver record: NOAA X-ray start/peak/end values are separate context, not substitutes. Preserve original estimates when the observer makes corrections, and exclude unreviewed candidates from a submission-ready monthly table.

Retain observer/receiver identity, transmitter/frequency, sampling cadence, original voltage records and configuration provenance with each event; add location only where required and consented. These supporting metadata are useful for traceability, but are not claimed to be additional mandatory columns in the published five-field BAA table. A local CSV can serve as an application export, not a purported BAA-mandated CSV format. Check any additional observer identifiers, preferred attachment format and treatment of events crossing UT midnight before finalizing submission instructions.

## 14. Delivery sequence and acceptance checks

Implement in small, testable stages:

1. **Tracked foundation and hardware acquisition:** establish the VLF source/configuration contract, installer skeleton, shared logging/UTC helpers and an ADC Pi collector service.
2. **Local data products:** correct the data-integrity findings in section 5, then add deterministic daily processing, exact rolling-window processing, GNUplot rendering and the static dashboard.
3. **Operational installation:** complete repeatable install/update behavior, scheduling locks, permissions, log rotation, freshness reporting and recovery documentation.
4. **Opt-in integrations:** add remote upload and validated VLF candidate alerts, testing failure isolation and notification state.
5. **Reporting compatibility:** implement observer review and a monthly five-field BAA-style report; confirm the importance scale and any additional submission conventions before automating classification. Keep submission manual unless separately agreed and supported.

The final release should demonstrate the following, rather than relying on syntax checks alone:

| Check | Expected evidence |
|---|---|
| Clean deployment | Download a clean GitHub release onto the target Zero 2 W and complete installation with the documented single command, without access to the ignored examples tree. |
| Hardware reads | Verify configured I2C addresses/channel and readings against known safe voltages within the receiver range; record ADC mode/gain and measurement tolerance. Confirm that read failures are visible and never become zero-valued observations. |
| Configuration/history | Changing station/frequency changes new labels/metadata, rejects invalid settings, and does not relabel earlier observations. |
| Daily correctness | UTC day boundaries, leap days, New Year and safe reruns are covered; missing/reordered NOAA bands cannot create mismatched samples. |
| Exact rolling output | With a fixed end boundary, output spans exactly the preceding 24 hours with 1,440 minute bins, including missing bins; exclude a sample exactly at the end and include one exactly at the start. Test midnight, month/year rollover, partial startup and retuning. |
| Five-minute delivery | Observe successive scheduled generation/publication cycles on the actual Pi. Each normally completes within five minutes, overlapping jobs cannot corrupt outputs, and the browser displays the new generation rather than a cached image. |
| Resource suitability | Measure memory, CPU, disk growth and job duration on the Zero 2 W while collection and web serving continue; do not infer suitability solely from a desktop run. |
| Local dashboard | A second device on the home LAN can view plots/status and download data; required page assets still load without internet access. Secrets are not served. |
| Failure recovery | Reboot, ADC disconnect, missing input files, full/unwritable output storage and interrupted rendering produce explicit errors/stale status without invented data or partially published files. Reconnection/restart restores operation. |
| Optional services | With FTP/email disabled, there are no connection attempts. When enabled, upload/SMTP failures leave collection and local plots intact; repeated evaluation of one candidate does not send duplicate successful alerts. |
| Scientific review | Evaluate candidate detection using labelled VLF examples, including dips, enhancements, daylight transitions and transmitter outages; report false positives/limitations before promoting alerts as scientifically useful. |
| BAA report preparation | Export a reviewed month's observations with Date, Start, Peak, End and Importance in UT. Preserve unknown end times and unassigned importance without fabricating values; exclude unreviewed candidates and do not substitute NOAA flare times for receiver-observed SID times. |

This addendum updates the report only. Application implementation, Raspberry Pi installation, performance measurements, event-threshold selection and BAA report generation remain subsequent work; the BAA importance rules still require confirmation.
