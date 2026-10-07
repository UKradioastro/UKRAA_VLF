#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================

# Program to scrape the sunrise and sun set times
# From https://sunrise-sunset.org/api

# ==========================================================================================
#
# INFORMATION FROM WEBSITE
#
# ==========================================================================================

#
# Sunset and sunrise times API
#
# We offer a free API that provides sunset and sunrise times for a given latitude and longitude.
# 
# Please note that attribution is required if you use our API. Check "Usage limits and attribution" section below for more information.
# 
# API documentation
#      Ours is a very simple REST api, you only have to do a GET request to https://api.sunrise-sunset.org/json.
# 
# Parameters
#      lat (float): Latitude in decimal degrees. Required.
#      lng (float): Longitude in decimal degrees. Required.
#      date (string): Date in YYYY-MM-DD format. Also accepts other date formats and even relative date formats. If not present, date defaults to current date. Optional.
#      callback (string): Callback function name for JSONP response. Optional.
#      formatted (integer): 0 or 1 (1 is default). Time values in response will be expressed following ISO 8601 and day_length will be expressed in seconds. Optional.
# 
# Sample requests
#
# These are three sample requests for getting sunset and sunrise information from our API for a given location:# GetDataSun - program
#      https://api.sunrise-sunset.org/json?lat=36.7201600&lng=-4.4203400
#      https://api.sunrise-sunset.org/json?lat=36.7201600&lng=-4.4203400&date=today
#      https://api.sunrise-sunset.org/json?lat=36.7201600&lng=-4.4203400&date=2020-07-25
#      https://api.sunrise-sunset.org/json?lat=36.7201600&lng=-4.4203400&formatted=0
#
# Response
#      The result data is formatted using JSON. An example:
# 
# NOTE: All times are in UTC and summer time adjustments are not included in the returned data.
#
# {
#       "results":
#       {
#         "sunrise":"7:27:02 AM",
#         "sunset":"5:05:55 PM",
#         "solar_noon":"12:16:28 PM",
#         "day_length":"9:38:53",
#         "civil_twilight_begin":"6:58:14 AM",
#         "civil_twilight_end":"5:34:43 PM",
#         "nautical_twilight_begin":"6:25:47 AM",
#         "nautical_twilight_end":"6:07:10 PM",
#         "astronomical_twilight_begin":"5:54:14 AM",
#         "astronomical_twilight_end":"6:38:43 PM"
#       },
#        "status":"OK"
#     }
# 
#
# Response without date formatting:
# 
#     {
#       "results":
#       {
#         "sunrise":"2015-05-21T05:05:35+00:00",
#         "sunset":"2015-05-21T19:22:59+00:00",
#         "solar_noon":"2015-05-21T12:14:17+00:00",
#         "day_length":51444,
#         "civil_twilight_begin":"2015-05-21T04:36:17+00:00",
#         "civil_twilight_end":"2015-05-21T19:52:17+00:00",
#         "nautical_twilight_begin":"2015-05-21T04:00:13+00:00",
#         "nautical_twilight_end":"2015-05-21T20:28:21+00:00",
#         "astronomical_twilight_begin":"2015-05-21T03:20:49+00:00",
#         "astronomical_twilight_end":"2015-05-21T21:07:45+00:00"
#       },
#        "status":"OK"
#     }
#
# Status codes
#   The "status" field within the API response object contains the status of the request. The "status" field may contain the following values:
# 
#      "OK": indicates that no errors occurred;
#      "INVALID_REQUEST": indicates that either lat or lng parameters are missing or invalid;
#      "INVALID_DATE": indicates that date parameter is missing or invalid;
#      "UNKNOWN_ERROR": indicates that the request could not be processed due to a server error. The request may succeed if you try again.
#

# ==========================================================================================
#
# PROGRAM CODE
#
# ==========================================================================================

# import 
import requests
import json
from datetime import date, time, datetime
import os
import os.path

# Set up the parameters we want to pass to the API.
#
# This is the latitude and longitude of N15 London.
#
# Latitude (deg) = 51.587222
# Latitude (DMS) = 51° 35' 14" N
#
# Longitude (deg) = -0.095000
# Longitude (DMS) = 00° 05' 42" W
#
# date=today
#
# formatted=0  
#
# Make a get request with the parameters.
#

AddressURL = 'https://api.sunrise-sunset.org/json?lat=51.587222&lng=-0.095000&date=today&formatted=0'

response = requests.get(AddressURL,verify=True)

# ==========================================================================================
#
# Test response by printing request data
#
# ==========================================================================================
# Print the content of the response (the data the server returned)
# uncomment next line to print the response
#print()
#print(response.content)
#print()

# ==========================================================================================
#
# END SECTION- happy - can request data for today and location
#
#  Now want to extract sunrise and sunset from scrapped data
#
# ==========================================================================================


# ==========================================================================================
#
# TEST - extract date, sunrise time and sunset times - and convert to datetime format
#
# ==========================================================================================

data = json.loads(response.content)

# 2020-07-25T19:58:42+00:00 structure of return
# 1234567890123456789012345 character position for using [x:x] to get data from JSON file

# extract sunrise data from JSON
SunRise = data['results']['sunrise']

# convert sunrise and sunset data to datetime.time class
SunRiseDay = date(int(SunRise[0:4]), int(SunRise[5:7]), int(SunRise[8:10]))
SunRiseTimeUTC = time(int(SunRise[11:13]), int(SunRise[14:16]))

# check data correct format
# uncomment next lines to print the response
#print()
#print("Checking data extracted from json and format of variable - variable names in parentheses")
#print("Value of variable (SunRiseDay): ",SunRiseDay)
#print("Data type of variable (SunRiseDay): ",type(SunRiseDay))
#print("Value of variable (SunRise): ",SunRise)
#print("Data type of variable (SunRise): ",type(SunRise))
#print("Value of variable (SunRiseTimeUTC): ",SunRiseTimeUTC)
#print("Data type of variable (SunRiseTimeUTC): ",type(SunRiseTimeUTC))
#print()
#print("Test concatenation of extracted data")
#print("The sun rises at ",SunRiseTimeUTC,"UTC on ",SunRiseDay)
#print()


# extract sunset data from JSON
SunSet = data['results']['sunset']

# convert sunrise and sunset data to datetime.time class
SunSetDay = date(int(SunSet[0:4]), int(SunSet[5:7]), int(SunSet[8:10]))
SunSetTimeUTC = time(int(SunSet[11:13]), int(SunSet[14:16]))

# check data correct format
# uncomment next line to print the response
#print()
#print("Checking data extracted from json and format of variable - variable names in parentheses")
#print("Value of variable (SunSetDay): ",SunSetDay)
#print("Data type of variable (SunSetDay): ",type(SunSetDay))
#print("Value of variable (SunSet): ",SunSet)
#print("Data type of variable (SunSet): ",type(SunSet))
#print("Value of variable (SunSetTimeUTC): ",SunSetTimeUTC)
#print("Data type of variable (SunSetTimeUTC): ",type(SunSetTimeUTC))
#print()
#print("Test concatenation of extracted data")
#print("The sun sets at ",SunSetTimeUTC,"UTC on ",SunSetDay)
#print()

# ==========================================================================================
#
# END SECTION- happy - extracts sunrise and sunset data from json
#
#  Now want to get todays date for file naming
#
# ==========================================================================================


# ==========================================================================================
#
# TEST - get today's date as a string to be able to write to file latter
#
# ==========================================================================================

# Get today from datetime.now and check type
today = datetime.now()
# check data correct format
# uncomment next lines to print the response
#print()
#print("Value of variable (today): ",today)
#print("Data type of variable (today): ",type(today))
#print()

# check data correct format code - year
# uncomment next lines to print the response
#TodayYear = today.strftime("%Y")
#print()
#print("Value of variable (TodayYear): ",TodayYear)
#print("Data type of variable (TodayYear): ",type(TodayYear))
#print()

# check data correct format code - month
# uncomment next lines to print the response
#TodayMonth = today.strftime("%m")
#print()
#print("Value of variable (TodayMonth): ",TodayMonth)
#print("Data type of variable (TodayMonth): ",type(TodayMonth))
#print()

# check data correct format code - day
# uncomment next lines to print the response
#TodayDay = today.strftime("%d")
#print()
#print("Value of variable (TodayDay): ",TodayDay)
#print("Data type of variable (TodayDay): ",type(TodayDay))
#print()

# Convert today from datetime.now to string
TodaySTR = today.strftime("%Y-%m-%d")

# check data correct format code - %Y-%m-%d
# uncomment next lines to print the response
#print()
#print("Value of variable (TodaySTR): ",TodaySTR)
#print("Data type of variable (TodaySTR): ",type(TodaySTR))
#print()

# check data correct format
# uncomment next lines to print the response
#todayINT=int(today.strftime('%Y%m%d'))
#print()
#print(todayINT)
#print(type(todayINT))
#print()


# ==========================================================================================
#
# END TEST- happy - gets todays date in string format for using latter
#
#  Now want to create file structure based on year, month
#
# ==========================================================================================


# ==========================================================================================
#
# TEST - need to check if SunRise directory exists - if not - create, if it does - do nothing
#
# ==========================================================================================
#
# define some functions that will be called latter in the program


def GetPathnameYear():
    # Use current date to get a text string of "Path/YYYY" for today.
    # Used to create PathNameY
    # uncomment next lines to print the response and check working correctly
    #print()
    #print ("check if GetPathnameYear is working: ",Path + datetime.strftime(datetime.now(), '%Y'))
    #print()
    return Path + datetime.strftime(datetime.now(), '%Y')

def GetPathnameYearMonth():
    # Use current date to get a text string of "PathNameY/YYYY-mm for today.
    # used to create PathNameYm
    # uncomment next lines to print the response and check working correctly
    #print()
    #print ("check if GetPathnameYearMonth is working: ",PathNameY + "/" + datetime.strftime(datetime.now(), '%Y-%m'))
    #print()
    return PathNameY + "/" + datetime.strftime(datetime.now(), '%Y-%m')

def GetFilenameYearMonthDay():
    # Use current date to get a text string of "PathNameYm/YYY-mm-dd.txt" for today
    # used to create FileNameYmd
    # uncomment next lines to print the response and check working correctly
    #print()
    #print ("check if GetFilenameYearMonthDay is working: ",datetime.strftime(datetime.now(), '%Y-%m-%d') + ".txt")
    #print()
    return datetime.strftime(datetime.now(), '%Y-%m-%d') + ".txt"

def CheckFolderYear():
    #check have year folder first
    if os.path.isdir(folderY):
        # If folderY does exist - do nothing
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Year folder exists in data folder")
        #print()
        CheckFolderY = "Year folder already exists" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Done nothing")
        #print()
        return CheckFolderY
    else:
        # If folderY does not exist - create it
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Year folder doesn't exists in data folder")
        #print()
        os.mkdir(folderY)
        CheckFolderY = "Year folder now created" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Made Year folder directory")
        #print()
        return CheckFolderY
    
def CheckFolderMonth():
    #check have year folder first
    if os.path.isdir(folderYm):
        # If folderYm does exist - do nothing
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Month folder exists in Year folder data folder")
        #print()
        CheckFolderYm = "Month folder already exists in year folder" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Done nothing")
        #print()
        return CheckFolderYm
    else:
        # If folderYm does not exist - create it
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Month folder doesn't exists in Year folder")
        #print()
        os.mkdir(folderYm)
        CheckFolderYm = "Month folder now created in year folder" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Made month folder in Year folder")
        #print()
        return CheckFolderYm

# ==========================================================================================
#
# END TEST- happy - definitions created -
#
# Now try for SunRise file structure
#
# ==========================================================================================
#
# Path parameters for SunRise data file structure
#
# Path = /home/pi/VLF/data/SunRise/
# PathNameY = /home/pi/VLF/data/SunRise/YYYY
# PathNameYm:  /home/pi/VLF/data/SunRise/YYYY/YYYY-MM
# FileNameYmd:  YYYY-MM-DD.txt
# SunRisePathFileNameYmd /home/pi/VLF/data/SunRise/YYYY/YYYY-MM/YYYY-MM-DD.txt

# Set start path for SunRise data file structure
Path = "/home/pi/VLF/data/SunRise/"
# uncomment next lines to print the response
#print()
#print("Value of variable ~SunRise~ (Path): ",Path)
#print("Data type of variable ~SunRise~(Path): ",type(Path))
#print()


# Add year variable to path for SunRise data file structure
PathNameY = GetPathnameYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (PathNameY): ",PathNameY)
#print("Data type of variable (PathNameY): ",type(PathNameY))
#print()

# Add yearmonth variable to path for SunRise data file structure
PathNameYm = GetPathnameYearMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (PathNameYm): ",PathNameYm)
#print("Data type of variable (PathNameY): ",type(PathNameY))
#print()

# Make filemane of txt file to write SunRise data to
FileNameYmd = GetFilenameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (FileNameYmd): ",FileNameYmd)
#print("Data type of variable (FileNameYmd): ",type(FileNameYmd))
#print()

# check full path and filename for writing SunRise data to
SunRisePathFileNameYmd = PathNameYm + "/" + FileNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (SunRisePathFileNameYmd): ",SunRisePathFileNameYmd)
#print("Data type of variable (SunRisePathFileNameYmd): ",type(SunRisePathFileNameYmd))
#print()

# Year folder needs creating??
folderY = PathNameY
# uncomment next lines to print the response
#print()
#print("Value of variable (folderY): ",folderY)
#print("Data type of variable (folderY): ",type(folderY))
#print()

folderY = CheckFolderYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (folderY) after: ",folderY)
#print("Data type of variable (folderY): ",type(folderY))
#print()

# Month folder needs creating??
folderYm = PathNameYm
# uncomment next lines to print the response
#print()
#print("Value of variable (folderYm): ",folderYm)
#print("Data type of variable (folderYm): ",type(folderYm))
#print()
folderYm = CheckFolderMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (folderYm) after: ",folderYm)
#print("Data type of variable (folderYm): ",type(folderYm))
#print()


# ==========================================================================================
#
# END TEST- happy - file structure checked and pathnames created for write function
#
# now write SunRise data files
#
# ==========================================================================================


# ==========================================================================================
#
# TEST - write SunRise data to path/file (text file)
#
# ==========================================================================================

# variables in this section
# date: "TodaySTR"
# path and name of file = "SunRisePathFileNameYmd"
# date of data: "SunRiseDay"
# sunrise time @ UTC : "SunRiseTimeUTC"

# text file location
SunData= open(SunRisePathFileNameYmd,'a+')
SunData.write(str(TodaySTR))                    # today's date
SunData.write(" ")                              # space separator
SunData.write(str(SunRiseTimeUTC))              # sun rise time UTC
SunData.write(",")                              # , separator
SunData.write ("Sunrise time (UTC) London UK")  # Set label for gnuplot
SunData.write("\n")                             # new line
SunData.close()

# print statement to logfile to say that sunrise and sunset data has been scraped and saved
print('Completed SunRise data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# ==========================================================================================
#
# END TEST- happy - writes SunRise data to file
#
# now do same for SunSet data
#
# ==========================================================================================

#
# Path parameters for SunSet data file structure
#
# Path = /home/pi/VLF/data/SunSet/
# PathNameY = /home/pi/VLF/data/SunSet/YYYY
# PathNameYm:  /home/pi/VLF/data/SunSet/YYYY/YYYY-MM
# FileNameYmd:  YYYY-MM-DD.txt
# SunSetPathFileNameYmd /home/pi/VLF/data/SunSet/YYYY/YYYY-MM/YYYY-MM-DD.txt

# Set start path for SunSet data file structure
Path = "/home/pi/VLF/data/SunSet/"
# uncomment next lines to print the response
#print()
#print("Value of variable ~SunSet~ (Path): ",Path)
#print("Data type of variable ~SunSet~ (Path): ",type(Path))
#print()


# Add year variable to path for SunRise data file structure
PathNameY = GetPathnameYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (PathNameY): ",PathNameY)
#print("Data type of variable (PathNameY): ",type(PathNameY))
#print()

# Add yearmonth variable to path for SunRise data file structure
PathNameYm = GetPathnameYearMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (PathNameYm): ",PathNameYm)
#print("Data type of variable (PathNameY): ",type(PathNameY))
#print()

# Make filemane of txt file to write SunRise data to
FileNameYmd = GetFilenameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (FileNameYmd): ",FileNameYmd)
#print("Data type of variable (FileNameYmd): ",type(FileNameYmd))
#print()

# check full path and filename for writing SunRise data to
SunSetPathFileNameYmd = PathNameYm + "/" + FileNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (SunSetPathFileNameYmd): ",SunSetPathFileNameYmd)
#print("Data type of variable (SunSetPathFileNameYmd): ",type(SunSetPathFileNameYmd))
#print()

# Year folder needs creating??
folderY = PathNameY
# uncomment next lines to print the response
#print()
#print("Value of variable (folderY): ",folderY)
#print("Data type of variable (folderY): ",type(folderY))
#print()

folderY = CheckFolderYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (folderY) after: ",folderY)
#print("Data type of variable (folderY): ",type(folderY))
#print()

# Month folder needs creating??
folderYm = PathNameYm
# uncomment next lines to print the response
#print()
#print("Value of variable (folderYm): ",folderYm)
#print("Data type of variable (folderYm): ",type(folderYm))
#print()
folderYm = CheckFolderMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (folderYm) after: ",folderYm)
#print("Data type of variable (folderYm): ",type(folderYm))
#print()


# ==========================================================================================
#
# END TEST- happy - file structure checked and pathnames created for write function
#
# now write SunSet data files
#
# ==========================================================================================


# ==========================================================================================
#
# TEST - write SunSet data to path/file (text file)
#
# ==========================================================================================

# variables in this section
# date: "TodaySTR"
# path and name of file = "SunSetPathFileNameYmd"
# date of data: "SunSetDay"
# sunrise time @ UTC : "SunSetTimeUTC"

SunData= open(SunSetPathFileNameYmd,'a+')
SunData.write(str(TodaySTR))                    # today's date
SunData.write(" ")                              # space separator
SunData.write(str(SunSetTimeUTC))               # sun rise time UTC
SunData.write(",")                              # , separator
SunData.write ("Sunset time (UTC) London UK")   # Set label for gnuplot
SunData.write("\n")                             # new line
SunData.close()

# print statement to logfile to say that sunrise and sunset data has been scraped and saved
print('Completed SunSet data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# ==========================================================================================
#
# END -
#
# Now really happy
# - scrapes sunrise and sunset data from https://sunrise-sunset.org/api
# - extracts the sunrise time and the sunset time from the JSON
# - corrects UTC to LocalTime (GMT/BST) - no longer used all in UTC see below
# - creates file name based on year and then year month
# - checks that there is a year folder - if not create one
# - checks that there is a month folder - if not creates one
# - writes data to file (txt) in format: date (YYY-MM-DD), sunrise time (HH:MM:SS) and sunset time (HH:MM:SS)
#
# - MODIFICATION = KEEP TIMES AS UTC TO MATCH XRAY DATA
# - now keeps sunrise and sunset times in UTC
#
# - runs via CRON each day at 2.10AM
#   crontab entry  "10 2 * * * /usr/bin/python3 /home/pi/VLF/scripts/GetDataSun.py> /home/pi/VLF/LogFiles/cron-sun.log 2>&1"
#   
# ==========================================================================================