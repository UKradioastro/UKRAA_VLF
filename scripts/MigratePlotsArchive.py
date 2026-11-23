#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================
#
# One-off migration of the plot archive to the restructured layout.
# Run manually once after upgrading an existing installation:
#
#   python3 /home/pi/UKRAA-VLF/scripts/MigratePlotsArchive.py [--dry-run]
#
# What it does:
#   - moves the old yesterday-plot archive files
#         <data>/Plots/VLFplot<hz>-YYYYMMDD.png
#         <data>/Plots/NOAAxraysYesterday-YYYYMMDD.png
#     into the new date-structured archive
#         <plots>/<CALLSIGN>/day/YYYY/YYYY-MM/<hz>-YYYY-MM-DD.png
#         <plots>/NOAA/day/YYYY/YYYY-MM/NOAA-YYYY-MM-DD.png
#     (the callsign for each frequency comes from config/aerials.ini;
#     files for frequencies no longer configured are left in place)
#   - removes the empty <data>/Plots folder afterwards
#   - deletes the old flat-layout PNGs from the temp folder (the plot
#     scripts now write into the rolling/ and periods/ subfolders)
#
# Safe to re-run; --dry-run reports what would be done without changing
# anything. Actions are also logged to logfiles/logfile.log.
#
# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

import argparse
import glob
import os
import re
import sys
from datetime import datetime

from vlf_common import (load_aerials, load_paths, log_message,
                        plot_archive_path)

SOURCE = 'MigratePlotsArchive.py'

OLD_ARCHIVE_PATTERN = re.compile(
    r'^(?:VLFplot(?P<hz>\d+)|(?P<noaa>NOAAxraysYesterday))'
    r'-(?P<date>\d{8})\.png$')

# Old flat-layout plot names in the temp folder root
OLD_TEMP_GLOBS = ['VLFrolling*.png', 'VLFplot*.png', 'VLF3day*.png',
                  'VLF7day*.png', 'NOAAxrays*.png']


def parse_args():
    parser = argparse.ArgumentParser(
        description='Migrate the plot archive to the restructured layout.')
    parser.add_argument('--dry-run', action='store_true',
                        help='report what would be done without changing '
                             'anything')
    return parser.parse_args()


def main():
    args = parse_args()
    paths = load_paths()
    logfiles_path = paths['logfiles']
    plots_path = paths['plots']
    old_archive = os.path.join(paths['data'], 'Plots')

    def act(message):
        prefix = 'Would ' if args.dry_run else ''
        print(f'{prefix}{message}' if prefix else message)
        if not args.dry_run:
            log_message(logfiles_path, SOURCE, message)

    callsigns = {str(station['frequency_hz']): station['callsign']
                 for station in load_aerials()['stations']}

    # Move the old date-stamped yesterday plots into the new archive tree
    moved = skipped = 0
    if os.path.isdir(old_archive):
        for name in sorted(os.listdir(old_archive)):
            match = OLD_ARCHIVE_PATTERN.match(name)
            if not match:
                print(f'Leaving unrecognised file {name} in {old_archive}')
                skipped += 1
                continue
            try:
                day = datetime.strptime(match['date'], '%Y%m%d').date()
            except ValueError:
                print(f'Leaving file with invalid date {name} in '
                      f'{old_archive}')
                skipped += 1
                continue
            if match['noaa']:
                station_folder = stem = 'NOAA'
            else:
                station_folder = callsigns.get(match['hz'])
                stem = match['hz']
                if not station_folder:
                    print(f'Leaving {name} in {old_archive} - frequency '
                          f'{match["hz"]} Hz is not in aerials.ini')
                    skipped += 1
                    continue
            source = os.path.join(old_archive, name)
            if args.dry_run:
                target = os.path.join(plots_path, station_folder, 'day',
                                      f'{day:%Y}', f'{day:%Y-%m}',
                                      f'{stem}-{day:%Y-%m-%d}.png')
                act(f'move {source} to {target}')
            else:
                target = plot_archive_path(plots_path, station_folder,
                                           'day', day, stem)
                os.replace(source, target)
                act(f'Moved {source} to {target}')
            moved += 1
        if not args.dry_run and not os.listdir(old_archive):
            os.rmdir(old_archive)
            act(f'Removed empty folder {old_archive}')
    else:
        print(f'No old archive folder at {old_archive} - nothing to move')

    # Remove the old flat-layout plots from the temp folder root
    removed = 0
    for pattern in OLD_TEMP_GLOBS:
        for path in sorted(glob.glob(os.path.join(paths['temp'], pattern))):
            if args.dry_run:
                act(f'delete old temp plot {path}')
            else:
                os.remove(path)
                act(f'Deleted old temp plot {path}')
            removed += 1

    print(f'Migration {"preview" if args.dry_run else "complete"}: '
          f'{moved} archive file(s) moved, {skipped} left in place, '
          f'{removed} old temp plot(s) deleted')
    return 0


if __name__ == '__main__':
    sys.exit(main())
