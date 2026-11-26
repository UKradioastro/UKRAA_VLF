#!/bin/bash

# checkNetwork.sh - WiFi/network watchdog. Runs every 5 minutes via cron.
#
# The Pi Zero 2W's WiFi can drop out and never come back (brcmfmac driver
# hang), leaving the Pi running but unreachable until it is power-cycled.
# This watchdog pings the default gateway; after consecutive failures it
# bounces the WiFi interface, and if that still does not restore
# connectivity it reboots the Pi as a last resort (aerial capture restarts
# automatically - it is a systemd service - and the cron jobs catch up).
#
# install/install.sh grants the passwordless sudo needed for ip/iw/reboot
# (/etc/sudoers.d/ukraa-vlf) and disables WiFi power saving, the usual
# trigger for the dropouts.
#
# Silent while the network is healthy. Failures and recovery actions are
# logged to logerror.log, recovery confirmations to logfile.log.

# base path is the parent of the scripts folder this file lives in
BASE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$BASE_PATH/logfiles"
STATE_FILE="$LOG_DIR/checkNetwork.state"
SOURCE_NAME="checkNetwork.sh"

# bounce the WiFi after this many consecutive failed checks, reboot after
# this many more (with cron every 5 minutes: bounce at ~5 min, reboot at
# ~15 min of outage)
BOUNCE_AFTER=1
REBOOT_AFTER=3
# never reboot twice within this window, so a dead router/broadband outage
# (which a reboot cannot fix) does not cause a reboot loop
REBOOT_COOLDOWN_SECONDS=3600

log_entry() {
    printf '%s UTC : %-27s : %s\n' \
        "$(date -u '+%Y-%m-%d %H:%M:%S')" "$SOURCE_NAME" "$2" \
        >> "$LOG_DIR/$1"
}

mkdir -p "$LOG_DIR"

# only useful on a WiFi Pi - exit quietly on wired-only setups
WIFI_INTERFACE=""
for device in /sys/class/net/*; do
    if [ -d "$device/wireless" ]; then
        WIFI_INTERFACE=$(basename "$device")
        break
    fi
done
if [ -z "$WIFI_INTERFACE" ]; then
    exit 0
fi

# previous state: consecutive failures, last-known gateway (the default
# route vanishes when the WiFi dies, so it must be remembered from a
# healthy check) and the time of the last watchdog reboot
failures=0
gateway=""
last_reboot=0
if [ -f "$STATE_FILE" ]; then
    # shellcheck disable=SC1090
    . "$STATE_FILE"
fi

save_state() {
    printf 'failures=%s\ngateway=%s\nlast_reboot=%s\n' \
        "$failures" "$gateway" "$last_reboot" > "$STATE_FILE"
}

current_gateway=$(ip route show default 2>/dev/null | awk '/^default/ {print $3; exit}')
if [ -n "$current_gateway" ]; then
    gateway=$current_gateway
fi

# healthy if the gateway answers ping
if [ -n "$gateway" ] && ping -n -q -c 2 -W 3 "$gateway" >/dev/null 2>&1; then
    if [ "$failures" -gt 0 ]; then
        log_entry logfile.log "Network restored after $failures failed check(s) - gateway $gateway reachable again"
    fi
    failures=0
    save_state
    exit 0
fi

failures=$((failures + 1))
if [ -n "$gateway" ]; then
    reason="gateway $gateway not answering ping"
else
    reason="no default gateway known"
fi

if [ "$failures" -ge "$REBOOT_AFTER" ]; then
    now=$(date -u +%s)
    if [ $((now - last_reboot)) -ge "$REBOOT_COOLDOWN_SECONDS" ]; then
        log_entry logerror.log "Network check failed ($failures consecutive): $reason - WiFi bounce did not recover it, REBOOTING"
        last_reboot=$now
        failures=0
        save_state
        sync
        sudo -n reboot
        exit 0
    fi
    log_entry logerror.log "Network check failed ($failures consecutive): $reason - reboot skipped (last watchdog reboot under $((REBOOT_COOLDOWN_SECONDS / 60)) min ago), bouncing WiFi $WIFI_INTERFACE again"
else
    log_entry logerror.log "Network check failed ($failures consecutive): $reason - bouncing WiFi $WIFI_INTERFACE"
fi
save_state

if [ "$failures" -ge "$BOUNCE_AFTER" ]; then
    sudo -n ip link set "$WIFI_INTERFACE" down
    sleep 5
    sudo -n ip link set "$WIFI_INTERFACE" up
    # re-assert power saving off - WiFi power save is the usual cause of
    # the Pi Zero 2W dropouts
    sudo -n iw dev "$WIFI_INTERFACE" set power_save off 2>/dev/null
fi
