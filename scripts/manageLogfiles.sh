#!/bin/bash

# manageLogfiles.sh - keeps older copies of the shared VLF log files.
# Rotates logfile.log and logerror.log, keeping three previous generations
# (-0 newest ... -2 oldest). Runs once per week (Sunday 00:30 UTC) via cron.
#
# All log entry timestamps are UTC, matching the Python scripts.

# base path is the parent of the scripts folder this file lives in
BASE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$BASE_PATH/logfiles"
MAIN_LOG="$LOG_DIR/logfile.log"

log_msg() {
    printf '%s UTC : %-27s : %s\n' \
        "$(date -u '+%Y-%m-%d %H:%M:%S')" "manageLogfiles.sh" "$1" \
        >> "$MAIN_LOG"
}

mkdir -p "$LOG_DIR"
cd "$LOG_DIR" || exit 1

log_msg "Started rotating log files"

for name in logfile logerror; do
    # oldest generation drops off; everything shuffles down one place
    [ -f "$name-1.log" ] && mv -f "$name-1.log" "$name-2.log"
    [ -f "$name-0.log" ] && mv -f "$name-0.log" "$name-1.log"
    [ -f "$name.log" ]   && mv -f "$name.log"   "$name-0.log"
    : > "$name.log"
done

log_msg "Completed rotating log files - previous logs kept as -0 (newest) to -2 (oldest)"
