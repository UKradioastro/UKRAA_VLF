#!/bin/bash
# ==========================================================================================
#
# UKRAA VLF - web server install section
#
# Installs Apache and publishes the intranet page that displays the rolling
# and yesterday plots. Intended to be incorporated into (or sourced from)
# the main VLF install.sh once that is written; it can also be run on its
# own for testing:
#
#   sudo bash /home/pi/UKRAA-VLF/install/install_webserver.sh
#
# What it does:
#   - installs apache2 (no PHP or database is needed - the page is static
#     HTML that reads temp/plots.json written by the plot scripts)
#   - copies WWW/index.html and WWW/images to /var/www/html
#   - creates /var/www/html/temp owned by the pi user
#   - points the [paths] temp entry in config/vlf.ini at /var/www/html/temp/
#     so the plot scripts write their PNGs and plots.json straight into the
#     served folder - no copy step or symlink is needed
#
# ==========================================================================================

set -e

# Defaults match the standard install; the main install.sh can override
# these before sourcing this file.
BASE_PATH="${BASE_PATH:-/home/pi/UKRAA-VLF}"
FILE_OWNER="${FILE_OWNER:-pi}"
FILE_GROUP="${FILE_GROUP:-$FILE_OWNER}"
WWW_ROOT="${WWW_ROOT:-/var/www/html}"

if [ "$(id -u)" -ne 0 ]; then
	echo "This script must be run as root (use sudo)."
	exit 1
fi

if [ ! -f "$BASE_PATH/WWW/index.html" ]; then
	echo "Cannot find $BASE_PATH/WWW/index.html - check BASE_PATH."
	exit 1
fi

echo "Start installing web server on RPi..."
echo ""

echo "Update packages..."
apt update
echo "Finished updating packages"
echo ""

echo "Install apache2..."
apt install apache2 -y
echo "Finished installing apache2"
echo ""

echo "Publish web page to $WWW_ROOT..."
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
VLF_INI="$BASE_PATH/config/vlf.ini"
if [ -f "$VLF_INI" ]; then
	sed -i "s|^temp = .*|temp = $WWW_ROOT/temp/|" "$VLF_INI"
	echo "Updated temp path in $VLF_INI"
else
	echo "WARNING: $VLF_INI not found - set 'temp = $WWW_ROOT/temp/'"
	echo "         in the [paths] section once the config file exists."
fi
echo ""

echo "Restart apache2..."
service apache2 restart
echo "Restarted apache2 service"
echo ""

echo "Finished installing web server on RPi"
echo "The page will show plots once the plotting cron jobs have run"
echo "(rolling plots refresh every 5 minutes)."
echo ""
