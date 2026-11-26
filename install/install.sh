#!/bin/bash
# ==========================================================================================
#
# UKRAA VLF - installer
#
# Installs the UKRAA VLF software, all its dependencies, the aerial capture
# systemd service, the cron jobs and the intranet web server. Designed to
# run unattended - no questions are asked.
#
# Run from the checkout as the account that should own the installation:
#
#   sudo bash ~/UKRAA_VLF/install/install.sh
#
# The installation account is the account that invoked sudo (it does not
# have to be "pi"); override with VLF_FILE_OWNER when running from a root
# login:
#
#   sudo VLF_FILE_OWNER=myaccount bash /home/myaccount/UKRAA_VLF/install/install.sh
#
# The installation base path is wherever this checkout lives - all paths in
# the configuration, crontab and systemd service are set from it, so any
# username and directory name work.
#
# Safe to re-run: existing configuration files are kept, packages already
# present are skipped by apt, and the service/crontab entries are replaced.
#
# ==========================================================================================

if [ "$(id -u)" -ne 0 ]; then
	echo "Run the installer with sudo." >&2
	exit 1
fi

FILE_OWNER=${VLF_FILE_OWNER:-${SUDO_USER:-}}
if [ -z "$FILE_OWNER" ] || [ "$FILE_OWNER" = root ] || ! id "$FILE_OWNER" >/dev/null 2>&1; then
	echo "Specify a non-root installation account with sudo or VLF_FILE_OWNER." >&2
	exit 1
fi

USER_HOME=$(getent passwd "$FILE_OWNER" | cut -d: -f6)
BASE_PATH=$(readlink -f "$(dirname "${BASH_SOURCE[0]}")/..")
if [ -z "$USER_HOME" ] || [[ ! "$BASE_PATH" =~ ^/[A-Za-z0-9_./-]+$ ]]; then
	echo "Unsupported installation path: $BASE_PATH" >&2
	echo "(only letters, digits, dots, underscores, hyphens and slashes are supported)" >&2
	exit 1
fi
if [ "$(stat -c %U "$BASE_PATH")" != "$FILE_OWNER" ]; then
	echo "The installation directory $BASE_PATH must be owned by $FILE_OWNER." >&2
	exit 1
fi
FILE_GROUP=$(id -gn "$FILE_OWNER")

NEW_VERSION=$(cat "$BASE_PATH/VERSION" 2>/dev/null || echo "unknown")
INSTALLED_VERSION_FILE="$BASE_PATH/config/installed-version.txt"
OLD_VERSION=""
if [ -f "$INSTALLED_VERSION_FILE" ]; then
	OLD_VERSION=$(cat "$INSTALLED_VERSION_FILE")
fi

if [ -z "$OLD_VERSION" ]; then
	echo "Fresh install: v$NEW_VERSION"
elif [ "$OLD_VERSION" = "$NEW_VERSION" ]; then
	echo "Re-running install for existing v$NEW_VERSION (no version change)"
else
	echo "Upgrading UKRAA VLF: v$OLD_VERSION -> v$NEW_VERSION"
fi
echo "Installing to $BASE_PATH for account $FILE_OWNER"
echo ""

echo "Start installing UKRAA VLF software..."
echo ""


# ------------------------------------------------------------------------------------------
# Software dependencies
# ------------------------------------------------------------------------------------------

echo "Update packages..."
apt update
echo "Finished updating packages"
echo ""

echo "Install dependencies (gnuplot, python3-requests, i2c-tools, smbus2)..."
apt install -y gnuplot
apt install -y python3-requests
apt install -y i2c-tools
# smbus2 is needed by scripts/ADCPi.py (vendored ABElectronics ADC Pi
# library); older OS releases only package the legacy python3-smbus,
# which ADCPi.py also accepts
apt install -y python3-smbus2 || apt install -y python3-smbus
echo "Finished installing dependencies"
echo ""


# ------------------------------------------------------------------------------------------
# System configuration: I2C bus and UTC clock
# ------------------------------------------------------------------------------------------

echo "Enable the I2C interface (used by the ADC Pi board)..."
if command -v raspi-config >/dev/null 2>&1; then
	raspi-config nonint do_i2c 0
	modprobe i2c-dev 2>/dev/null
	echo "I2C interface enabled"
else
	echo "WARNING: raspi-config not found - enable I2C manually if the"
	echo "         ADC Pi is not detected (Interface Options -> I2C)"
fi
echo ""

echo "Set the system timezone to UTC (all data/log timestamps are UTC)..."
if command -v timedatectl >/dev/null 2>&1; then
	timedatectl set-timezone Etc/UTC
	echo "Timezone set to UTC"
else
	echo "WARNING: timedatectl not found - set the timezone to UTC manually"
fi
echo ""


# ------------------------------------------------------------------------------------------
# System configuration: WiFi reliability (power save off + watchdog sudo)
# ------------------------------------------------------------------------------------------

# The Pi Zero 2W's WiFi driver can hang and never reconnect, leaving the
# Pi running but unreachable until it is power-cycled. Two defences:
#  - disable WiFi power saving, the usual trigger for the dropouts
#  - grant the passwordless sudo that the network watchdog cron job
#    (scripts/checkNetwork.sh) needs to bounce the WiFi interface and,
#    as a last resort, reboot the Pi

echo "Disable WiFi power saving (prevents Pi Zero 2W WiFi dropouts)..."
if [ -d /etc/NetworkManager ]; then
	# Bookworm and later manage WiFi with NetworkManager
	cat > /etc/NetworkManager/conf.d/ukraa-vlf-wifi-powersave-off.conf <<- 'EOF'
	# Installed by UKRAA VLF install.sh - keep WiFi power saving off
	# (the Pi Zero 2W WiFi tends to drop out and not recover with it on)
	[connection]
	wifi.powersave = 2
	EOF
	systemctl reload NetworkManager 2>/dev/null || true
	echo "NetworkManager configured (wifi.powersave = 2)"
elif command -v iw >/dev/null 2>&1; then
	# older OS releases (dhcpcd/wpa_supplicant): oneshot unit applies it
	# on every boot once the network is up
	cat > /etc/systemd/system/ukraa-vlf-wifi-powersave.service <<- 'EOF'
	# Installed by UKRAA VLF install.sh - keep WiFi power saving off
	[Unit]
	Description=UKRAA VLF - disable WiFi power saving
	After=network.target

	[Service]
	Type=oneshot
	ExecStart=/bin/sh -c 'for d in /sys/class/net/*/wireless; do [ -d "$d" ] && iw dev "$(basename "$(dirname "$d")")" set power_save off; done'

	[Install]
	WantedBy=multi-user.target
	EOF
	systemctl daemon-reload
	systemctl enable --now ukraa-vlf-wifi-powersave.service 2>/dev/null || true
	echo "Systemd unit installed (ukraa-vlf-wifi-powersave.service)"
else
	echo "WARNING: neither NetworkManager nor iw found - disable WiFi"
	echo "         power saving manually if the WiFi connection drops out"
fi
# apply immediately for this session too
if command -v iw >/dev/null 2>&1; then
	for wireless_dir in /sys/class/net/*/wireless; do
		if [ -d "$wireless_dir" ]; then
			iw dev "$(basename "$(dirname "$wireless_dir")")" set power_save off 2>/dev/null || true
		fi
	done
fi
echo ""

echo "Grant the network watchdog its sudo permissions (/etc/sudoers.d/ukraa-vlf)..."
cat > /etc/sudoers.d/ukraa-vlf <<- EOF
	# Installed by UKRAA VLF install.sh - lets the network watchdog cron
	# job (scripts/checkNetwork.sh, run as $FILE_OWNER) bounce the WiFi
	# interface and reboot the Pi when connectivity cannot be restored
	$FILE_OWNER ALL=(root) NOPASSWD: /usr/sbin/ip, /sbin/ip, /usr/sbin/iw, /sbin/iw, /usr/sbin/reboot, /sbin/reboot
EOF
chmod 440 /etc/sudoers.d/ukraa-vlf
if ! visudo -cf /etc/sudoers.d/ukraa-vlf >/dev/null; then
	echo "Invalid sudoers file generated - removing it" >&2
	rm -f /etc/sudoers.d/ukraa-vlf
	exit 1
fi
echo "Watchdog sudo permissions installed"
echo ""


# ------------------------------------------------------------------------------------------
# Directory structure and log files
# ------------------------------------------------------------------------------------------

echo "Creating UKRAA VLF directory structure..."
for directory in config data logfiles plots temp; do
	sudo -u "$FILE_OWNER" mkdir -vp "$BASE_PATH/$directory"
done
echo "UKRAA VLF directory structure created"
echo ""

echo "Provide RPi desktop wallpaper..."
sudo -u "$FILE_OWNER" mkdir -p "$USER_HOME/Pictures"
sudo -u "$FILE_OWNER" cp -v "$BASE_PATH/images/UKRAA_VLF_wallpaper.jpg" \
	"$USER_HOME/Pictures/UKRAA_VLF_wallpaper.jpg"
echo "RPi desktop wallpaper provided, ~/Pictures/UKRAA_VLF_wallpaper.jpg"
echo ""

echo "Creating UKRAA VLF log files..."
for logFile in logfile.log logerror.log; do
	sudo -u "$FILE_OWNER" touch "$BASE_PATH/logfiles/$logFile"
done
chown -v "$FILE_OWNER:$FILE_GROUP" "$BASE_PATH/logfiles" "$BASE_PATH"/logfiles/*
chmod -v 664 "$BASE_PATH"/logfiles/*
echo "UKRAA VLF log files created"
echo ""


# ------------------------------------------------------------------------------------------
# Configuration files
# ------------------------------------------------------------------------------------------

# Copy <name>.ini.example to config/<name>.ini unless it already exists
# (re-runs and upgrades keep the user's settings), replacing the example
# /home/pi/UKRAA-VLF paths with the real installation path.
set_up_configuration() {
	local description=$1
	local name=$2
	local template_path="$BASE_PATH/install/$name.ini.example"
	local config_path="$BASE_PATH/config/$name.ini"

	echo "Set up $description configuration..."
	if [ ! -f "$config_path" ]; then
		sudo -u "$FILE_OWNER" cp -v "$template_path" "$config_path"
		sudo -u "$FILE_OWNER" sed -i "s|/home/pi/UKRAA-VLF|$BASE_PATH|g" "$config_path"
		echo "Created $config_path"
	else
		echo "Retaining existing values in $config_path"
	fi
	echo ""
}

set_up_configuration "paths" vlf
set_up_configuration "station location" user
set_up_configuration "aerials / ADC" aerials
set_up_configuration "plot" plots
set_up_configuration "alert" alerts
set_up_configuration "remote upload" remote-upload
set_up_configuration "BAA SID report" baa-report


# ------------------------------------------------------------------------------------------
# MCP3424 (ADC Pi) I2C address detection
# ------------------------------------------------------------------------------------------

# The two MCP3424 chips on the ADC Pi answer in the 0x68-0x6F range
# (position set by the board's address jumpers). Detect them and write
# the addresses into config/aerials.ini so the capture service works
# without manual configuration.
echo "Detecting MCP3424 ADC chips on the I2C bus..."
AERIALS_INI="$BASE_PATH/config/aerials.ini"
DETECTED_ADDRESSES=()
if [ -e /dev/i2c-1 ] && command -v i2cdetect >/dev/null 2>&1; then
	while read -r address; do
		DETECTED_ADDRESSES+=("0x$address")
	done < <(i2cdetect -y 1 2>/dev/null \
		| sed -n 's/^60: //p' \
		| tr ' ' '\n' \
		| grep -iE '^6[89a-f]$')
fi
if [ "${#DETECTED_ADDRESSES[@]}" -ge 2 ]; then
	echo "Found MCP3424 chips at: ${DETECTED_ADDRESSES[*]}"
	sudo -u "$FILE_OWNER" sed -i \
		-e "s|^address_1 = .*|address_1 = ${DETECTED_ADDRESSES[0]}|" \
		-e "s|^address_2 = .*|address_2 = ${DETECTED_ADDRESSES[1]}|" \
		"$AERIALS_INI"
	echo "Updated address_1/address_2 in $AERIALS_INI"
elif [ "${#DETECTED_ADDRESSES[@]}" -eq 1 ]; then
	echo "WARNING: only one MCP3424 found (${DETECTED_ADDRESSES[0]}) - expected two."
	echo "         Check the ADC Pi is seated correctly, then confirm the"
	echo "         addresses with: i2cdetect -y 1"
	echo "         and set address_1/address_2 in $AERIALS_INI"
else
	echo "WARNING: no MCP3424 found on I2C bus 1 (addresses 0x68-0x6F)."
	echo "         If I2C was just enabled a reboot may be needed first."
	echo "         Confirm the addresses with: i2cdetect -y 1"
	echo "         and set address_1/address_2 in $AERIALS_INI"
fi
echo ""


# ------------------------------------------------------------------------------------------
# File permissions
# ------------------------------------------------------------------------------------------

echo "Sort out UKRAA VLF file permissions..."
sudo -u "$FILE_OWNER" chmod -v +x "$BASE_PATH"/scripts/*.py
sudo -u "$FILE_OWNER" chmod -v +x "$BASE_PATH"/scripts/*.sh
echo "UKRAA VLF file permissions sorted out"
echo ""


# ------------------------------------------------------------------------------------------
# Aerial capture systemd service
# ------------------------------------------------------------------------------------------

echo "Installing the aerial capture service (ukraa-vlf-aerial.service)..."
sed -e "s|User=pi|User=$FILE_OWNER|" \
	-e "s|/home/pi/UKRAA-VLF|$BASE_PATH|g" \
	"$BASE_PATH/install/ukraa-vlf-aerial.service" \
	> /etc/systemd/system/ukraa-vlf-aerial.service
systemctl daemon-reload
if ! systemctl enable --now ukraa-vlf-aerial.service; then
	echo "Failed to enable/start ukraa-vlf-aerial.service" >&2
	exit 1
fi
echo "Aerial capture service installed and started"
echo "(check with: systemctl status ukraa-vlf-aerial.service)"
echo ""


# ------------------------------------------------------------------------------------------
# Crontab
# ------------------------------------------------------------------------------------------

echo "Start installing UKRAA VLF crontab entries for $FILE_OWNER..."
tmpCronFile=$(mktemp)
# keep any unrelated entries; drop previous UKRAA VLF entries (both the
# standard-path ones and any pointing at this installation)
crontab -u "$FILE_OWNER" -l 2>/dev/null | grep -vE 'UKRAA[-_]VLF' \
	| grep -vF "$BASE_PATH/scripts" > "$tmpCronFile"
sed "s|/home/pi/UKRAA-VLF|$BASE_PATH|g" "$BASE_PATH/install/crontabVLF.cron" >> "$tmpCronFile"
crontab -u "$FILE_OWNER" "$tmpCronFile"
rm -f "$tmpCronFile"
echo "UKRAA VLF crontab entries installed"
echo ""


# ------------------------------------------------------------------------------------------
# Web server (Apache + intranet page)
# ------------------------------------------------------------------------------------------

# Installs Apache and publishes the static intranet page that displays the
# rolling and yesterday plots (no PHP or database is needed - the page
# reads temp/plots.json written by the plot scripts), then points the
# [paths] temp entry in config/vlf.ini at the served folder so the plot
# scripts write their PNGs and plots.json straight into it - no copy step
# or symlink is needed.
WWW_ROOT=/var/www/html

echo "Start installing web server on RPi..."
echo ""

echo "Install apache2..."
apt install -y apache2
echo "Finished installing apache2"
echo ""

echo "Publish web page to $WWW_ROOT..."
if [ ! -f "$BASE_PATH/WWW/index.html" ]; then
	echo "Cannot find $BASE_PATH/WWW/index.html - checkout incomplete?" >&2
	exit 1
fi
cp -v "$BASE_PATH/WWW/index.html" "$WWW_ROOT/index.html"
cp -vr "$BASE_PATH/WWW/images" "$WWW_ROOT/"
echo "Finished publishing web page"
echo ""

echo "Create served temp folder for plots..."
mkdir -pv "$WWW_ROOT/temp"
chown -v "$FILE_OWNER:$FILE_GROUP" "$WWW_ROOT/temp"
echo "Finished creating served temp folder"
echo ""

echo "Point config/vlf.ini temp path at $WWW_ROOT/temp/..."
sudo -u "$FILE_OWNER" sed -i "s|^temp = .*|temp = $WWW_ROOT/temp/|" "$BASE_PATH/config/vlf.ini"
echo "Updated temp path in $BASE_PATH/config/vlf.ini"
echo ""

echo "Restart apache2..."
if ! systemctl restart apache2; then
	echo "Failed to restart apache2" >&2
	exit 1
fi
echo "Restarted apache2 service"
echo ""

echo "Finished installing web server on RPi"
echo ""


# ------------------------------------------------------------------------------------------
# Finish up
# ------------------------------------------------------------------------------------------

echo "$NEW_VERSION" | sudo -u "$FILE_OWNER" tee "$INSTALLED_VERSION_FILE" > /dev/null

SHORT_HOSTNAME=$(hostname -s)
echo "Completed installing UKRAA VLF software (v$NEW_VERSION)."
echo ""
echo "Next steps:"
echo "  - set your station name/latitude/longitude in $BASE_PATH/config/user.ini"
echo "  - set the callsign/frequency for each connected channel in $AERIALS_INI"
echo "  - optional: email alerts in $BASE_PATH/config/alerts.ini, extra plots in"
echo "    $BASE_PATH/config/plots.ini, FTP upload in $BASE_PATH/config/remote-upload.ini,"
echo "    BAA SID reports in $BASE_PATH/config/baa-report.ini"
echo "  - after editing aerials.ini restart the capture service:"
echo "      sudo systemctl restart ukraa-vlf-aerial.service"
echo "  - the plots page is at http://${SHORT_HOSTNAME,,}.local (plots appear"
echo "    once the 5-minute cron jobs have run)"
