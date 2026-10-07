#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================

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

# ==========================================================================================
#
# INFORMATION FROM WEBSITE and scripts provided
#
# ==========================================================================================

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



# ==========================================================================================
#
#  Import function
#
# ==========================================================================================

import time
from datetime import datetime, timedelta, timezone
import os


# ==========================================================================================
#
#  Use definitions
#
# ======================================================================

def main():
    
    def get_filename_year():
        # Use current date to get a text string of "Path/YYYY" for today.
        # Used to create PathNameY
        #print ("check if get_filename_year is working: ",Path + datetime.strftime(datetime.now(), '%Y'))
        return Path + datetime.strftime(datetime.now(timezone.utc), '%Y')
    
    def get_filename_yearmonth():
        # Use current date to get a text string of "PathNameY/YYYY-mm for today.
        # used to create PathNameYm
        #print ("check if get_filename_yearmonth is working: ",PathNameY + "/" + datetime.strftime(datetime.now(), '%Y-%m'))
        return PathNameY + "/" + datetime.strftime(datetime.now(timezone.utc), '%Y-%m')
    
    def get_filename_yearmonthday():
        # Use current date to get a text string of "PathNameYm/YYY-mm-dd.txt" for today
        # used to create FileNameYmd
        #print ("check if get_filename_yearmonthday is working: ",datetime.strftime(datetime.now(), '%Y-%m-%d') + ".txt")
        return datetime.strftime(datetime.now(timezone.utc), '%Y-%m-%d') + ".txt"
    
    def check_folder_year():
        #check have year folder first
        if os.path.isdir(folderY):
            #print("Year Folder Exists")
            CheckFolderY = "TRUE" # random variable write
            #print("Done nothing")
            return CheckFolderY
        else:
            #print("Year folder doesn't exists")
            os.mkdir(folderY)
            CheckFolderY = "Year folder now Created" # random variable write
            #print("Made Year folder directory")
            return CheckFolderY
    
    def check_folder_month():
        #check have year folder first
        if os.path.isdir(folderYm):
            #print("Month folder exists in Year folder")
            CheckFolderYm = "TRUE" # random variable write
            #print("Done nothing")
            return CheckFolderYm
        else:
            #print("Month folder doesn't exists in Year folder")
            os.mkdir(folderYm)
            CheckFolderYm = "Month folder now Created" # random variable write
            #print("Made month folder in Year folder")
            return CheckFolderYm
        
    def writetofile(texttowrite):
        #    Open the data file, write the value and close the file.
        file = open(PathFileNameYmd, 'a')
        #print(file)
        #print(type(file))
        file.write(datetime.strftime(datetime.now(timezone.utc), '%Y-%m-%d') + " " + datetime.strftime(datetime.now(timezone.utc), '%H:%M:%S') + "," + texttowrite)
        file.close()

    while True:
            adc = ADCPi(0x68, 0x69, 12)
            # Get full path for writing for today
            Path = "/home/pi/VLF/data/Aerial/"
            # Get full path for writing for today
            PathNameY = get_filename_year()
            # Get full path for writing for today
            PathNameYm = get_filename_yearmonth()
            # Get full path for writing for today
            FileNameYmd = get_filename_yearmonthday()
            PathFileNameYmd = PathNameYm + "/" + FileNameYmd
            # Year folder needs creating??
            folderY = PathNameY
            folderY = check_folder_year()
            # Month folder needs creating??
            folderYm = PathNameYm
            folderYm = check_folder_month()
            #print ("Time: ",time.asctime()," File: ",PathFileNameYmd)
            # read from adc channels and write to the log file
            writetofile("%.4f\n" % adc.read_voltage(1))
            # wait for start of next minute before reading the pins again
            time.sleep(60.0 - ((time.time()) % 60.0))                 # without starttime
        
    
    
# ==========================================================================================
#
# Loop program to run all the time
#
# ==========================================================================================


if __name__ == "__main__":
    main()
    
# ==========================================================================================
#
# END of program
#
# ==========================================================================================