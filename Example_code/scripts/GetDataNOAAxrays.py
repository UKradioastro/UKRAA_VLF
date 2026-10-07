#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================

# program to get the daily GOES X-ray flux data from NOAA
# data available as 
# 1-day data : https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json
# 3-day data : https://services.swpc.noaa.gov/json/goes/primary/xrays-3-day.json
#
# data has format for both files
#   time_tag    yyyy-mm-ddThh:mm:ssZ
#   satellite   xx
#   flux    x.xxxxxxxxxxxxExxx
#   energy  0.05-0.4nm & 0.1-0.8nm
#
# data is recorded every minute

# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

# ==========================================================================================
#
# imports
#
# ==========================================================================================

import requests
import json
from datetime import datetime
import os

import configparser

config = configparser.ConfigParser()
config.read('/home/pi/VLF/data/vlfdata.ini')
#print(config.sections())
path = (config ['paths'] ['data'] )
#print(path)
y = (config ['calender_yesterday'] ['year'] )
#print(y)
ym = (config ['calender_yesterday'] ['yearmonth'] )
#print(ym)
ymd = (config ['calender_yesterday'] ['yearmonthday'] )
#print(ymd)



# ==========================================================================================
#
# Define functions
#
# used for folder structure
#
# note this is going to store data for "yesterday" so using date now - timedelta(1)
#
# ==========================================================================================
def CheckFolderData():
    #check have year folder first
    if os.path.isdir(folderD):
        # If folderD does exist - do nothing
        # uncomment next lines to print the response and check working correctly
        #print("Data folder exists in data folder")
        #print()
        Action = "Data folder already exists" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print("Done nothing")
        #print()
        return Action
    else:
        # If folderY does not exist - create it
        # uncomment next lines to print the response and check working correctly
        #print("Year folder doesn't exists in data folder")
        #print()
        os.mkdir(folderD)
        Action = "Data folder now created" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print("Made Year folder directory")
        #print()
        return Action
    
def CheckFolderSource():
    #check have year folder first
    if os.path.isdir(folderS):
        # If folderS does exist - do nothing
        # uncomment next lines to print the response and check working correctly
        #print("Source folder exists in data folder")
        #print()
        Action = "Source folder already exists" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print("Done nothing")
        #print()
        return Action
    else:
        # If folderS does not exist - create it
        # uncomment next lines to print the response and check working correctly
        #print("Source folder doesn't exists in data folder")
        #print()
        os.mkdir(folderS)
        Action = "Source folder now created" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print("Made source folder directory")
        #print()
        return Action
    
def CheckFolderYear():
    #check have year folder first
    if os.path.isdir(folderY):
        # If folderY does exist - do nothing
        # uncomment next lines to print the response and check working correctly
        #print("Year folder exists in data folder")
        #print()
        Action = "Year folder already exists" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print("Done nothing")
        #print()
        return Action
    else:
        # If folderY does not exist - create it
        # uncomment next lines to print the response and check working correctly
        #print("Year folder doesn't exists in data folder")
        #print()
        os.mkdir(folderY)
        Action = "Year folder now created" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print("Made Year folder directory")
        #print()
        return Action
    
def CheckFolderMonth():
    #check have year folder first
    if os.path.isdir(folderYm):
        # If folderYm does exist - do nothing
        # uncomment next lines to print the response and check working correctly
        #print("Month folder exists in Year folder data folder")
        #print()
        Action = "Month folder already exists in year folder" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print("Done nothing")
        #print()
        return Action
    else:
        # If folderYm does not exist - create it
        # uncomment next lines to print the response and check working correctly
        #print("Month folder doesn't exists in Year folder")
        #print()
        os.mkdir(folderYm)
        Action = "Month folder now created in Year folder" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print("Made month folder in Year folder")
        #print()
        return Action

# print message to log file to say started
print('Started GOES primary xrays data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# ==========================================================================================
#
# X-ray data file structure
#
# If it is not there : create it
#
# If it is there : do nothing
#
# ==========================================================================================
#
# Path parameters for xray data file structure
#
# Path                : /home/pi/VLF/data/NOAAxray/
# PathNameY           : /home/pi/VLF/data/NOAAxray/primary/YYYY
# PathNameYm          : /home/pi/VLF/data/NOAAxray/primary/YYYY/YYYY-MM
# FileNameYmd         : YYYY-MM-DD.txt
# xrayPathFileNameYmd : /home/pi/VLF/data/NOAAxray/primary/YYYY/YYYY-MM/YYYY-MM-DD.txt

# Set start path for data file structure
PathData = path + 'NOAAxrays' + '/'
# Data folder needs creating??
folderD = PathData
# Call def CheckFolderData()
folderD = CheckFolderData()
# Set start path for data file structure
PathSource = PathData + 'primary' + '/'
# Source folder needs creating??
folderS = PathSource
# Call def CheckFolderSource()
folderS = CheckFolderSource()
# Add year variable to path for data file structure
PathNameY = PathSource + y + '/'
# Year folder needs creating??
folderY = PathNameY
# Call def CheckFolderYear()
folderY = CheckFolderYear()
# Add yearmonth variable to path for data file structure
PathNameYm = PathNameY + ym + '/'
# Month folder needs creating in year folder??
folderYm = PathNameYm
# Call def CheckFolderMonth()
folderYm = CheckFolderMonth()
# Make filemane of txt file to write data to
PathFileNameYmd = PathNameYm + ymd + '.txt'
# uncomment next lines to print the response
#print("Value of variable (PathFileNameYmd): ",PathFileNameYmd)
#print("Data type of variable (PathFileNameYmd): ",type(PathFileNameYmd))
#print()


# ==========================================================================================
#
# Get yesterdays date and store in variable "yesterdayString"
#
# Used when extracting data from JSON dictionary
#
# ==========================================================================================

# get yesterday's date in format wanted "YYYY-MM-DD" as string class
YesterdayString = ymd
# uncomment next lines to print the response
#print()
#print("Value of variable (YesterdayString): ",YesterdayString)
#print("Data type of variable (YesterdayString): ",type(YesterdayString))
#print("Yesterday's date was: ", YesterdayString)
#print()


# ==========================================================================================
#
# Get GOES 16 X-ray flux data from WWW
#
# ==========================================================================================
#
# Set up the parameters we want to pass to get data.
#
# Idea is to get 3-day JSON data and extract previous days data from it
# and then store it to a .txt file.
#
# 3-day data : https://services.swpc.noaa.gov/json/goes/primary/xrays-3-day.json
#
# primary data is from GOES 16
# secondary data is from GOES 17
#
# data has format for both files
#   time_tag    yyyy-mm-ddThh:mm:ssZ
#   satellite   xx
#   flux    x.xxxxxxxxxxxxExxx
#   energy  0.05-0.4nm & 0.1-0.8nm
#
# data is recorded every minute
#
# Make a get request with the parameters.
#

# variables
# URL variable of Scraped data
# GOES 16 data - used
#AddressURL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
AddressURL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-3-day.json"
# GOES 17 data - not used
#AddressURL = "https://services.swpc.noaa.gov/json/goes/secondary/xrays-1-day.json"
#AddressURL = "https://services.swpc.noaa.gov/json/goes/secondary/xrays-3-day.json"

response = requests.get(AddressURL, stream=True)

# pass this to variable for maniputation in program
#
# note used to save as temp file - now just processed in program
#

GOESData=json.loads(response.text)

# ==========================================================================================
#
# See what the response data is
#
# ==========================================================================================
# Print the content of the response (the data the server returned)
# uncomment next lines to print the response
#print()
#print("Variable content of (response.content): ","\n",response.content)
#print()
#print("Variable content of (response.text): ","\n",response.text)
#print()
#print("Variable content of (response.status_code): ","\n",response.status_code)
#print()
#print("Variable content of (response.encoding): ","\n",response.encoding)
#print()
#print("Variable content of (response.json()): ","\n",response.json())
#print()
#print("Variable content of (response.raw): ","\n",response.raw)
#print()
#print("Variable content of (response.raw.read(10)): ","\n",response.raw.read(10)) #????
#print()
#print("Variable content of (response.headers): ","\n",response.headers)
#print()
#print("Variable content of (response.headers['date']): ","\n",response.headers['date'])
#print()


# ==========================================================================================
#
# Extract data from JSON dictionary for yesterday
#
# Data variable used:
#     GOES16XrayData = JSON dictionary
#     yesterdayString = yesterdays date
#
# Data variable created:
#     XrayDateShort = date of data - format YYYY-MM-DD
#     XrayTimeShort = time of data - format HH:MM:SS
#     XrayFluxShort = data value   - format x.xxxxe-xx
#     XrayTagShort  = data energy  - format 0.05-0.4nm
#     XrayDateLong  = date of data - format YYYY-MM-DD
#     XrayTimeLong  = time of data - format HH:MM:SS
#     XrayFluxLong  = data value   - format x.xxxxe-xx
#     XrayTagLong   = data energy  - format 0.1-0.8nm
#

for Data in GOESData:
    # Print the content of the response (the data the server returned)
    # uncomment next lines to print the response
    #print()
    #print("Variable content of Proton['time_tag'] : ",Proton['time_tag'])
    #print("Variable content of Proton['satellite']: ",Proton['satellite'])
    #print("Variable content of Proton[flux']      : ",Proton['flux'])
    #print("Variable content of Proton['energy']   : ",Proton['energy'])
    
        
    # set up extracting yesterday's data from dictionary
    if Data['time_tag'][0:10] == YesterdayString:
        # extract 0.05-0.4nm X-ray data
        if Data['energy'] == "0.05-0.4nm":
            # variables created
            DataDateShort         = Data['time_tag'][0:10]          # format YYYY-MM-DD
            DataTimeShort         = Data['time_tag'][11:19]         # format HH:MM:SS
            DataSatelliteShort    = Data['satellite']               # format xx
            DataFluxShort         = '{:.4e}'.format(Data['flux'])   # format (xx)x.xxxxxx
            DataEnergyShort       = Data['energy']                  # format "0.05-0.4nm"
 
           # extract 0.1-0.8nm X-ray data
        elif Data['energy'] == "0.1-0.8nm":
            # variables created
            DataDateLong        = Data['time_tag'][0:10]          # format YYYY-MM-DD
            DataTimeLong        = Data['time_tag'][11:19]         # format HH:MM:SS
            DataSatelliteShort  = Data['satellite']               # format xx
            DataFluxLong        = '{:.4e}'.format(Data['flux'])   # format (xx)x.xxxxxx
            DataEnergyLong      = Data['energy']                  # format "0.1-0.8nm"

# ==========================================================================================
#
# Write data to path/file (text file)
#
# ==========================================================================================
#
# Variable list
#
# xrayPathFileNameYmd = file name and path
#
# XrayDateShort = date of data entry for 0.05-0.4nm X-ray flux data
# XrayTimeShort = time of data entry for 0.05-0.4nm X-ray flux data
# XrayFluxShort = value of data entry for 0.05-0.4nm X-ray flux data
# XrayTagShort  = name of data entry for 0.05-0.4nm X-ray flux data
#
# XrayDateLong = date of data entry for 0.1-0.8nm X-ray flux data
# XrayTimeLong = time of data entry for 0.1-0.8nm X-ray flux data
# XrayFluxLong = value of data entry for 0.1-0.8nm X-ray flux data
# XrayTagLong  = name of data entry for 0.1-0.8nm X-ray flux data
#

            # Write data to path/file (text file)
            file = open(PathFileNameYmd,'a+')
            file.write(str(DataDateShort))          # Data date
            file.write(" ")                          # " " separator
            file.write(str(DataTimeShort))          # Data time
            file.write(",")                          # , separator
            file.write(str(DataSatelliteShort))     # satellite number
            file.write(",")                          # , separator
            file.write(str(DataFluxShort))          # >=1MeV flux data value
            file.write(",")                          # , separator
            file.write(str(DataEnergyShort))        # Proton data energy
            file.write(",")                          # , separator
            file.write(str(DataFluxLong))          # >=1MeV flux data value
            file.write(",")                          # , separator
            file.write(str(DataEnergyLong))        # Proton data energy
            file.write("\n")                         # new line
            file.close()

# print message to log file to say completed
print('Completed GOES primary xrays data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# print message to log file to say started
print('Started GOES secondary xrays data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# ==========================================================================================
#
# X-ray data file structure
#
# If it is not there : create it
#
# If it is there : do nothing
#
# ==========================================================================================
#
# Path parameters for xray data file structure
#
# Path                : /home/pi/VLF/data/NOAAxray/
# PathNameY           : /home/pi/VLF/data/NOAAxray/primary/YYYY
# PathNameYm          : /home/pi/VLF/data/NOAAxray/primary/YYYY/YYYY-MM
# FileNameYmd         : YYYY-MM-DD.txt
# xrayPathFileNameYmd : /home/pi/VLF/data/NOAAxray/primary/YYYY/YYYY-MM/YYYY-MM-DD.txt

# Set start path for data file structure
PathData = path + 'NOAAxrays' + '/'
# Data folder needs creating??
folderD = PathData
# Call def CheckFolderData()
folderD = CheckFolderData()
# Set start path for data file structure
PathSource = PathData + 'secondary' + '/'
# Source folder needs creating??
folderS = PathSource
# Call def CheckFolderSource()
folderS = CheckFolderSource()
# Add year variable to path for data file structure
PathNameY = PathSource + y + '/'
# Year folder needs creating??
folderY = PathNameY
# Call def CheckFolderYear()
folderY = CheckFolderYear()
# Add yearmonth variable to path for data file structure
PathNameYm = PathNameY + ym + '/'
# Month folder needs creating in year folder??
folderYm = PathNameYm
# Call def CheckFolderMonth()
folderYm = CheckFolderMonth()
# Make filemane of txt file to write data to
PathFileNameYmd = PathNameYm + ymd + '.txt'
# uncomment next lines to print the response
#print("Value of variable (PathFileNameYmd): ",PathFileNameYmd)
#print("Data type of variable (PathFileNameYmd): ",type(PathFileNameYmd))
#print()


# ==========================================================================================
#
# Get yesterdays date and store in variable "yesterdayString"
#
# Used when extracting data from JSON dictionary
#
# ==========================================================================================

# get yesterday's date in format wanted "YYYY-MM-DD" as string class
YesterdayString = ymd
# uncomment next lines to print the response
#print()
#print("Value of variable (YesterdayString): ",YesterdayString)
#print("Data type of variable (YesterdayString): ",type(YesterdayString))
#print("Yesterday's date was: ", YesterdayString)
#print()


# ==========================================================================================
#
# Get GOES 16 X-ray flux data from WWW
#
# ==========================================================================================
#
# Set up the parameters we want to pass to get data.
#
# Idea is to get 3-day JSON data and extract previous days data from it
# and then store it to a .txt file.
#
# 3-day data : https://services.swpc.noaa.gov/json/goes/primary/xrays-3-day.json
#
# primary data is from GOES 16
# secondary data is from GOES 17
#
# data has format for both files
#   time_tag    yyyy-mm-ddThh:mm:ssZ
#   satellite   xx
#   flux    x.xxxxxxxxxxxxExxx
#   energy  0.05-0.4nm & 0.1-0.8nm
#
# data is recorded every minute
#
# Make a get request with the parameters.
#

# variables
# URL variable of Scraped data
# GOES 16 data - used
#AddressURL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
#AddressURL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-3-day.json"
# GOES 17 data - not used
#AddressURL = "https://services.swpc.noaa.gov/json/goes/secondary/xrays-1-day.json"
AddressURL = "https://services.swpc.noaa.gov/json/goes/secondary/xrays-3-day.json"

response = requests.get(AddressURL, stream=True)

# pass this to variable for maniputation in program
#
# note used to save as temp file - now just processed in program
#

GOESData=json.loads(response.text)

# ==========================================================================================
#
# See what the response data is
#
# ==========================================================================================
# Print the content of the response (the data the server returned)
# uncomment next lines to print the response
#print()
#print("Variable content of (response.content): ","\n",response.content)
#print()
#print("Variable content of (response.text): ","\n",response.text)
#print()
#print("Variable content of (response.status_code): ","\n",response.status_code)
#print()
#print("Variable content of (response.encoding): ","\n",response.encoding)
#print()
#print("Variable content of (response.json()): ","\n",response.json())
#print()
#print("Variable content of (response.raw): ","\n",response.raw)
#print()
#print("Variable content of (response.raw.read(10)): ","\n",response.raw.read(10)) #????
#print()
#print("Variable content of (response.headers): ","\n",response.headers)
#print()
#print("Variable content of (response.headers['date']): ","\n",response.headers['date'])
#print()


# ==========================================================================================
#
# Extract data from JSON dictionary for yesterday
#
# Data variable used:
#     GOES16XrayData = JSON dictionary
#     yesterdayString = yesterdays date
#
# Data variable created:
#     XrayDateShort = date of data - format YYYY-MM-DD
#     XrayTimeShort = time of data - format HH:MM:SS
#     XrayFluxShort = data value   - format x.xxxxe-xx
#     XrayTagShort  = data energy  - format 0.05-0.4nm
#     XrayDateLong  = date of data - format YYYY-MM-DD
#     XrayTimeLong  = time of data - format HH:MM:SS
#     XrayFluxLong  = data value   - format x.xxxxe-xx
#     XrayTagLong   = data energy  - format 0.1-0.8nm
#

for Data in GOESData:
    # Print the content of the response (the data the server returned)
    # uncomment next lines to print the response
    #print()
    #print("Variable content of Proton['time_tag'] : ",Proton['time_tag'])
    #print("Variable content of Proton['satellite']: ",Proton['satellite'])
    #print("Variable content of Proton[flux']      : ",Proton['flux'])
    #print("Variable content of Proton['energy']   : ",Proton['energy'])
    
        
    # set up extracting yesterday's data from dictionary
    if Data['time_tag'][0:10] == YesterdayString:
        # extract 0.05-0.4nm X-ray data
        if Data['energy'] == "0.05-0.4nm":
            # variables created
            DataDateShort         = Data['time_tag'][0:10]          # format YYYY-MM-DD
            DataTimeShort         = Data['time_tag'][11:19]         # format HH:MM:SS
            DataSatelliteShort    = Data['satellite']               # format xx
            DataFluxShort         = '{:.4e}'.format(Data['flux'])   # format (xx)x.xxxxxx
            DataEnergyShort       = Data['energy']                  # format "0.05-0.4nm"
 
           # extract 0.1-0.8nm X-ray data
        elif Data['energy'] == "0.1-0.8nm":
            # variables created
            DataDateLong        = Data['time_tag'][0:10]          # format YYYY-MM-DD
            DataTimeLong        = Data['time_tag'][11:19]         # format HH:MM:SS
            DataSatelliteShort  = Data['satellite']               # format xx
            DataFluxLong        = '{:.4e}'.format(Data['flux'])   # format (xx)x.xxxxxx
            DataEnergyLong      = Data['energy']                  # format "0.1-0.8nm"

# ==========================================================================================
#
# Write data to path/file (text file)
#
# ==========================================================================================
#
# Variable list
#
# xrayPathFileNameYmd = file name and path
#
# XrayDateShort = date of data entry for 0.05-0.4nm X-ray flux data
# XrayTimeShort = time of data entry for 0.05-0.4nm X-ray flux data
# XrayFluxShort = value of data entry for 0.05-0.4nm X-ray flux data
# XrayTagShort  = name of data entry for 0.05-0.4nm X-ray flux data
#
# XrayDateLong = date of data entry for 0.1-0.8nm X-ray flux data
# XrayTimeLong = time of data entry for 0.1-0.8nm X-ray flux data
# XrayFluxLong = value of data entry for 0.1-0.8nm X-ray flux data
# XrayTagLong  = name of data entry for 0.1-0.8nm X-ray flux data
#

            # Write data to path/file (text file)
            file = open(PathFileNameYmd,'a+')
            file.write(str(DataDateShort))          # Data date
            file.write(" ")                          # " " separator
            file.write(str(DataTimeShort))          # Data time
            file.write(",")                          # , separator
            file.write(str(DataSatelliteShort))     # satellite number
            file.write(",")                          # , separator
            file.write(str(DataFluxShort))          # >=1MeV flux data value
            file.write(",")                          # , separator
            file.write(str(DataEnergyShort))        # Proton data energy
            file.write(",")                          # , separator
            file.write(str(DataFluxLong))          # >=1MeV flux data value
            file.write(",")                          # , separator
            file.write(str(DataEnergyLong))        # Proton data energy
            file.write("\n")                         # new line
            file.close()

# print message to log file to say completed
print('Completed GOES secondary xrays data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))


# ==========================================================================================
#
# END of program
#
# ==========================================================================================
#
# - checks that there is a year folder - if not create one
# - checks that there is a month folder - if not creates one
# - creates file name based on year and then year month
# - scrapes magnet data from https://services.swpc.noaa.gov/json/goes/primary/magnetometers-3-day.json
# - extracts He, Hp, Hn and total magnetic flux magnitudes 
# - writes data to file (txt) in format:
# - format: date (YYYY-MM-DD) time (hh:mm:00), He magnetic flux (number), Hp magnetic flux (number), Hn magnetic flux (number), total magnetic flux (number), arcjet_flag (boolean)
#
#
# - runs via CRON each day at 2.20AM
#   crontab entry  "20 2 * * * /usr/bin/python3 /home/pi/VLF/scripts/GetDataMagnet.py> /home/pi/VLF/LogFiles/cron-Magnet.log 2>&1"
#
# ==========================================================================================