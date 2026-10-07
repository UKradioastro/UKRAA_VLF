#!/usr/bin/env python3

# INFORMATION

# Program to record data fro UKRAA VLF reciever using ABElectronics ADC hat
# 
# From https://www.abelectronics.co.uk
#
# ADC used : "ADC Pi" 
# ADC info : 8 x 17-bit 0 to 5V Single Ended Inputs
# ADC analogue channel addresses :
# 1-4 = I2C address 0x68
# 5-8 = I2C address 0x69
# jumper selection as per specification document

# ================================================
# ABElectronics ADC Pi 8-Channel ADC data-logger demo
# Requires python smbus to be installed
# run with: python demo_logvoltage.py
# ================================================
# Initialise the ADC device using the default addresses and sample rate, change
# this value if you have changed the address selection jumpers
# Sample rate can be 12,14, 16 or 18

from __future__ import absolute_import, division, print_function, \
                                                    unicode_literals

try:
    from ADCPi import ADCPi
except ImportError:
    print("Failed to import ADCPi from python system path")
    print("Importing from parent folder instead")
    try:
        import sys
        sys.path.append('..')
        from ADCPi import ADCPi
    except ImportError:
        raise ImportError(
            "Failed to import library from parent folder")

# Imports

import time
from datetime import datetime, timezone
import os

# Definitions
def main():
    
    def get_filename_year():
        return Path + datetime.strftime(datetime.now(timezone.utc), '%Y')
    
    def get_filename_yearmonth():
        return PathNameY + "/" + datetime.strftime(datetime.now(timezone.utc), '%Y-%m')
    
    def get_filename_yearmonthday():
        return datetime.strftime(datetime.now(timezone.utc), '%Y-%m-%d') + ".txt"
    
    def check_folder_year():
        if os.path.isdir(folderY):
            CheckFolderY = "TRUE" # random variable write
            return CheckFolderY
        else:
            os.mkdir(folderY)
            CheckFolderY = "Year folder now Created" # random variable write
            return CheckFolderY
    
    def check_folder_month():
        if os.path.isdir(folderYm):
            CheckFolderYm = "TRUE" # random variable write
            return CheckFolderYm
        else:
            os.mkdir(folderYm)
            CheckFolderYm = "Month folder now Created" # random variable write
            return CheckFolderYm
        
    def writetofile(texttowrite):
        file = open(PathFileNameYmd, 'a')
        file.write(datetime.strftime(datetime.now(timezone.utc), '%Y-%m-%d') + " " + datetime.strftime(datetime.now(timezone.utc), '%H:%M:%S') + "," + texttowrite)
        file.close()

    while True:
        adc = ADCPi(0x68, 0x69, 12)
        Path = "/home/pi/VLF/data/Aerial19600/"
        PathNameY = get_filename_year()
        PathNameYm = get_filename_yearmonth()
        FileNameYmd = get_filename_yearmonthday()
        PathFileNameYmd = PathNameYm + "/" + FileNameYmd
        folderY = PathNameY
        folderY = check_folder_year()
        folderYm = PathNameYm
        folderYm = check_folder_month()
        writetofile("%.4f\n" % adc.read_voltage(5))
        time.sleep(60.0 - ((time.time()) % 60.0)) # read every minute at 60 seconds

# main
if __name__ == "__main__":
    main()
