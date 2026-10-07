#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================

# program to get the events data from NOAA
# data available as 
# events data : https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json
#
# data has format
#
#     time_tag       : format = "yyyy-mm-ddThh:mm:ssZ"   : don't know what this is
#     begin_time     : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event start
#     begin_class    : format = "Ax.x"                   : class of event at start
#     max_time       : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event maximum
#     max_class      : format = "Ax.x"                   : class of event at maximum
#     max_xrlong     : format
#     max_ratio      : format
#     max_ratio_time : format
#     current_int_xrlong : format
#     end_time       : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event end
#     end_class      : format = "Ax.x"                   : class of event at end
#     satellite      : format = "xx"                    : satellite that detects event
#
# data is recorded every event

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
print('Started GOES primary xray flare events data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# ==========================================================================================
#
# Events data file structure
#
# If it is not there : create it
#
# If it is there : do nothing
#
# ==========================================================================================
#
# Path parameters for X-ray flares data file structure
#
# Path                  : /home/pi/VLF/data/NOAAxrayFlares/
# PathNameY             : /home/pi/VLF/data/NOAAxrayFlares/primary/YYYY
# PathNameYm            : /home/pi/VLF/data/NOAAxrayFlares/primary/YYYY/YYYY-MM
# FileNameYmd           : YYYY-MM-DD.txt
# EventsPathFileNameYmd : /home/pi/VLF/data/NOAAxrayFlares/primary/YYYY/YYYY-MM/YYYY-MM-DD.txt

# Set start path for data file structure
PathData = path + 'NOAAxrayFlares' + '/'
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
# Get NOAA events data from WWW
#
# ==========================================================================================
#
# Set up the parameters we want to pass to get data.
#
# Idea is to get events JSON data and extract previous days data from it
# and then store it to a .txt file.
#
# program to get the events data from NOAA
#
# data available as 
# events data : https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json
#
# data has format
#
#     time_tag       : format = "yyyy-mm-ddThh:mm:ssZ"   : don't know what this is
#     begin_time     : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event start
#     begin_class    : format = "Ax.x"                   : class of event at start
#     max_time       : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event maximum
#     max_class      : format = "Ax.x"                   : class of event at maximum
#     max_xrlong     : format
#     max_ratio      : format
#     max_ratio_time : format
#     current_int_xrlong : format
#     end_time       : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event end
#     end_class      : format = "Ax.x"                   : class of event at end
#     satellite      : format = "xx"                    : satellite that detects event
#
# data is recorded every event
#
# Make a get request with the parameters.
#

# variables
# URL variable of Scraped data
# Events data from NOAA - used
AddressURL = "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json"

#print("Getting data")

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
#     EventsData = JSON dictionary
#     yesterdayString = yesterdays date
#
# Data variable created:
#
#     EventDateStart = start date of event   - format YYYY-MM-DD
#     EventTimeStart = start time of event   - format HH:MM:SS
#     EventDateMax   = date of event maximum - format YYYY-MM-DD
#     EventTimeMax   = time of event maximum - format HH:MM:SS
#     EventDateEnd   = end date of event     - format YYYY-MM-DD
#     EventTimeEnd   = end time of event     - format HH:MM:SS
#     EventClass     = class of event        - format Ax.x
#


for Data in GOESData:
    # Print the content of the response (the data the server returned)
    # uncomment next lines to print the response
    #print()
    #print("Variable content of Data['time_tag'] : ",Data['time_tag'])
    #print("Variable content of Data['satellite']: ",Data['satellite'])
    #print("Variable content of Data[flux']      : ",Data['flux'])
    #print("Variable content of Data['energy']   : ",Data['energy'])
    
        
    # set up extracting yesterday's data from dictionary
    if Data['time_tag'][0:10] == YesterdayString:
        #set up variable to write to file
        DataDateStart    = Data['begin_time'][0:10]
        DataTimeStart    = Data['begin_time'][11:19]
        DataSatellite    = Data['satellite']               # format xx
        DataDateMax      = Data['max_time'][0:10]
        DataTimeMax      = Data['max_time'][11:19]
        DataDateEnd      = Data['end_time'][0:10]
        DataTimeEnd      = Data['end_time'][11:19]
        DataClass        = Data['max_class']
        DataFlux         = '{:.4e}'.format(Data['max_xrlong'])

        # ==========================================================================================
        #
        # Write data to path/file (text file)
        #
        # ==========================================================================================
        #
        # Variable list
        #
        # EventsPathFileNameYmd = file name and path
        #
        # EventDateStart = start date of event
        # EventTimeStart = start time of event
        # EventDateEnd   = end date of event
        # EventTimeEnd   = end time of event
        # EventClass     = class of event
        # EventFlux      = x-ray flux of event
        #

        file = open(PathFileNameYmd,'a+')
        file.write(str(DataDateMax))          # >=1MeV flux data value
        file.write(" ")                          # , separator
        file.write(str(DataTimeMax))        # Proton data energy
        file.write(",")                          # , separator
        file.write(str(DataFlux))        # Proton data energy
        file.write(",")                          # , separator
        file.write(str(DataDateStart))          # Data date
        file.write(" ")                          # " " separator
        file.write(str(DataTimeStart))          # Data time
        file.write(",")                          # , separator
        file.write(str(DataDateEnd))          # >=1MeV flux data value
        file.write(" ")                          # , separator
        file.write(str(DataTimeEnd))        # Proton data energy
        file.write(",")                          # , separator
        file.write(str(DataClass))          # >=1MeV flux data value
        file.write(",")                          # , separator
        file.write(str(DataSatellite))     # satellite number
        file.write("\n")                         # new line
        file.close()

# print message to log file to say completed
print('Completed GOES primary xray flare events data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# print message to log file to say started
print('Started GOES secondary xray flare events data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# ==========================================================================================
#
# Events data file structure
#
# If it is not there : create it
#
# If it is there : do nothing
#
# ==========================================================================================
#
# Path parameters for X-ray flares data file structure
#
# Path                  : /home/pi/VLF/data/NOAAxrayFlares/
# PathNameY             : /home/pi/VLF/data/NOAAxrayFlares/primary/YYYY
# PathNameYm            : /home/pi/VLF/data/NOAAxrayFlares/primary/YYYY/YYYY-MM
# FileNameYmd           : YYYY-MM-DD.txt
# EventsPathFileNameYmd : /home/pi/VLF/data/NOAAxrayFlares/primary/YYYY/YYYY-MM/YYYY-MM-DD.txt

# Set start path for data file structure
PathData = path + 'NOAAxrayFlares' + '/'
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
# Get NOAA events data from WWW
#
# ==========================================================================================
#
# Set up the parameters we want to pass to get data.
#
# Idea is to get events JSON data and extract previous days data from it
# and then store it to a .txt file.
#
# program to get the events data from NOAA
#
# data available as 
# events data : https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json
#
# data has format
#
#     time_tag       : format = "yyyy-mm-ddThh:mm:ssZ"   : don't know what this is
#     begin_time     : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event start
#     begin_class    : format = "Ax.x"                   : class of event at start
#     max_time       : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event maximum
#     max_class      : format = "Ax.x"                   : class of event at maximum
#     max_xrlong     : format
#     max_ratio      : format
#     max_ratio_time : format
#     current_int_xrlong : format
#     end_time       : format = "yyyy-mm-ddThh:mm:ssZ"   : date and time of event end
#     end_class      : format = "Ax.x"                   : class of event at end
#     satellite      : format = "xx"                    : satellite that detects event
#
# data is recorded every event
#
# Make a get request with the parameters.
#

# variables
# URL variable of Scraped data
# Events data from NOAA - used
AddressURL = "https://services.swpc.noaa.gov/json/goes/secondary/xray-flares-7-day.json"

#print("Getting data")

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
#     EventsData = JSON dictionary
#     yesterdayString = yesterdays date
#
# Data variable created:
#
#     EventDateStart = start date of event   - format YYYY-MM-DD
#     EventTimeStart = start time of event   - format HH:MM:SS
#     EventDateMax   = date of event maximum - format YYYY-MM-DD
#     EventTimeMax   = time of event maximum - format HH:MM:SS
#     EventDateEnd   = end date of event     - format YYYY-MM-DD
#     EventTimeEnd   = end time of event     - format HH:MM:SS
#     EventClass     = class of event        - format Ax.x
#


for Data in GOESData:
    # Print the content of the response (the data the server returned)
    # uncomment next lines to print the response
    #print()
    #print("Variable content of Data['time_tag'] : ",Data['time_tag'])
    #print("Variable content of Data['satellite']: ",Data['satellite'])
    #print("Variable content of Data[flux']      : ",Data['flux'])
    #print("Variable content of Data['energy']   : ",Data['energy'])
    
        
    # set up extracting yesterday's data from dictionary
    if Data['time_tag'][0:10] == YesterdayString:
        #set up variable to write to file
        DataDateStart    = Data['begin_time'][0:10]
        DataTimeStart    = Data['begin_time'][11:19]
        DataSatellite    = Data['satellite']               # format xx
        DataDateMax      = Data['max_time'][0:10]
        DataTimeMax      = Data['max_time'][11:19]
        DataDateEnd      = Data['end_time'][0:10]
        DataTimeEnd      = Data['end_time'][11:19]
        DataClass        = Data['max_class']
        DataFlux         = '{:.4e}'.format(Data['max_xrlong'])

        # ==========================================================================================
        #
        # Write data to path/file (text file)
        #
        # ==========================================================================================
        #
        # Variable list
        #
        # EventsPathFileNameYmd = file name and path
        #
        # EventDateStart = start date of event
        # EventTimeStart = start time of event
        # EventDateEnd   = end date of event
        # EventTimeEnd   = end time of event
        # EventClass     = class of event
        # EventFlux      = x-ray flux of event
        #

        file = open(PathFileNameYmd,'a+')
        file.write(str(DataDateMax))          # >=1MeV flux data value
        file.write(" ")                          # , separator
        file.write(str(DataTimeMax))        # Proton data energy
        file.write(",")                          # , separator
        file.write(str(DataFlux))        # Proton data energy
        file.write(",")                          # , separator
        file.write(str(DataDateStart))          # Data date
        file.write(" ")                          # " " separator
        file.write(str(DataTimeStart))          # Data time
        file.write(",")                          # , separator
        file.write(str(DataDateEnd))          # >=1MeV flux data value
        file.write(" ")                          # , separator
        file.write(str(DataTimeEnd))        # Proton data energy
        file.write(",")                          # , separator
        file.write(str(DataClass))          # >=1MeV flux data value
        file.write(",")                          # , separator
        file.write(str(DataSatellite))     # satellite number
        file.write("\n")                         # new line
        file.close()

# print message to log file to say completed
print('Completed GOES secondary xray flare events data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))


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