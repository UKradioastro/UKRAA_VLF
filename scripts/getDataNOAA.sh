#!/bin/bash

# getDataNOAA.sh - runs the NOAA data collection scripts consecutively so
# their logfile entries stay sequential rather than interleaved.
# Runs every 5 minutes via cron.

# base path is the parent of the scripts folder this file lives in
BASE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$BASE_PATH/scripts/GetDataNOAAxrays.py"
python3 "$BASE_PATH/scripts/GetDataNOAAxrayFlares.py"
