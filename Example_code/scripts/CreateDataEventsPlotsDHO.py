#!/usr/bin/env python3

# Code to create plots data from timings of X-ray flare events
#
# data used from events folder, xray folder and aerial folder
#
# using events data to get start time of event and end time of event
# and add hour either side of event to generate plot data
#
# Then get the data from both xray and aerial during these time periods
# Store these in txt files for plotting with gnuplot.
#


# imports
import csv
from datetime import datetime
from datetime import timedelta
import os

# =============================================================================
#
# List of variables used in code and meaning
#
#     EventsFieldNames  = ['EventMax', 'Flux', 'EventStart', 'EventEnd','Class']
#     SunRiseFieldNames = ['SunRiseTime', 'Location']
#     SunSetFieldNames  = ['SunRiseTime', 'Location']
#     XrayFieldNames    = ['XrayFluxTime', 'SoftXrayFlux', 'HardXrayFlux']
#     AerialFieldNames  = ['AerialTime', 'AerialValue']
#
#     EventsPath             = "/home/pi/VLF/data/Events/"
#     EventsPathNameY        = "/home/pi/VLF/data/Events/yyyy"
#     EventsPathNameYm       = "/home/pi/VLF/data/Events/yyyy/yyyy-mm" 
#     EventsFileNameYmd      = "yyyy-mm-dd.txt"
#     EventsPathFileNameYmd  = "/home/pi/VLF/data/Events/yyyy/yyyy-mm/yyyy-mm-dd.txt" 
#
#     SunRisePath            = "/home/pi/VLF/data/SunRise/"
#     SunRisePathNameY       = "/home/pi/VLF/data/SunRise/yyyy"
#     SunRisePathNameYm      = "/home/pi/VLF/data/SunRise/yyyy/yyyy-mm" 
#     SunRiseFileNameYmd     = "yyyy-mm-dd.txt"
#     SunRisePathFileNameYmd = "/home/pi/VLF/data/SunSet/yyyy/yyyy-mm/yyyy-mm-dd.txt" 
#
#     SunSetPath             = "/home/pi/VLF/data/SunSet/"
#     SunSetPathNameY        = "/home/pi/VLF/data/SunSet/yyyy"
#     SunSetPathNameYm       = "/home/pi/VLF/data/SunSet/yyyy/yyyy-mm" 
#     SunSetFileNameYmd      = "yyyy-mm-dd.txt"
#     SunSetPathFileNameYmd  = "/home/pi/VLF/data/SunSet/yyyy/yyyy-mm/yyyy-mm-dd.txt" 
#
#     XrayPath               = "/home/pi/VLF/data/xray/"
#     XrayPathNameY          = "/home/pi/VLF/data/xray/yyyy"
#     XrayPathNameYm         = "/home/pi/VLF/data/xray/yyyy/yyyy-mm" 
#     XrayFileNameYmd        = "yyyy-mm-dd.txt"
#     XrayPathFileNameYmd    = "/home/pi/VLF/data/xray/yyyy/yyyy-mm/yyyy-mm-dd.txt" 
#
#     AerialPath             = "/home/pi/VLF/data/Aerial/"
#     AerialPathNameY        = "/home/pi/VLF/data/Aerial/yyyy"
#     AerialPathNameYm       = "/home/pi/VLF/data/Aerial/yyyy/yyyy-mm" 
#     AerialFileNameYmd      = "yyyy-mm-dd.txt"
#     AerialPathFileNameYmd  = "/home/pi/VLF/data/Aerial/yyyy/yyyy-mm/yyyy-mm-dd.txt" 
#
#     SunRiseData            = get data from "SunRisePathFileNameYmd"
#     SunRiseStr             = yyyy-mm-dd hh:mm:ss of sunrise (string)
#     SunRiseDatetime        = yyyy-mm-dd hh:mm:ss of sunrise (datetime.datetime)
#
#     SunSetData            = get data from "SunRisePathFileNameYmd"
#     SunSetStr             = yyyy-mm-dd hh:mm:ss of sunrise (string)
#     SunSetDatetime        = yyyy-mm-dd hh:mm:ss of sunrise (datetime.datetime)
#
#
#     EventsLineCount       = number of events yesterday (integer)
#     PlotStartNumber       = number of events from yesterday after sunrise
#     PlotEndNumber         = number of events from yesterday after sunrise and before sunset
#     EventNumber           = number for each event from yesterday - index of event
#
# =============================================================================


# ==========================================================================================
#
# Define functions
#
# used for folder structure
#
# note this is going to store data for "yesterday" so using date now - timedelta(1)
#
# ==========================================================================================

def GetPathnameYear():
    # Use current date to get a text string of "Path/YYYY" for today.
    # Used to create DataPathNameY
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
    return PathNameY + "/" + datetime.strftime(datetime.now() - timedelta(1), '%Y-%m')

def GetPathnameYearMonthDay():
    # Use current date to get a text string of "PathNameY/YYYY-mm/YYYY-mm-dd for today.
    # used to create PathNameYmd
    # uncomment next lines to print the response and check working correctly
    #print()
    #print ("check if GetPathnameYearMonthDay is working: ",PathNameYm + "/" + datetime.strftime(datetime.now(), '%Y-%m-%d'))
    #print()
    return PathNameYm + "/" + datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    
def GetFilenameYearMonthDay():
    # Use current date to get a text string of "PathNameYm/YYY-mm-dd.txt" for today
    # used to create FileNameYmd
    # uncomment next lines to print the response and check working correctly
    #print()
    #print ("check if GetFilenameYearMonthDay is working: ",datetime.strftime(datetime.now(), '%Y-%m-%d') + ".txt")
    #print()
    return datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d') + ".txt"
    
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
    #check have month folder first
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
        CheckFolderYm = "Month folder now created in Year folder" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Made month folder in Year folder")
        #print()
        return CheckFolderYm

def CheckFolderDay():
    #check have day folder first
    if os.path.isdir(folderYmd):
        # If folderYmd does exist - do nothing
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Day folder exists in Month folder data folder")
        #print()
        CheckFolderYmd = "Day folder already exists in month folder" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Done nothing")
        #print()
        return CheckFolderYmd
    else:
        # If folderYmd does not exist - create it
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Day folder doesn't exists in Month folder")
        #print()
        os.mkdir(folderYmd)
        CheckFolderYmd = "Day folder now created in Year folder" # random variable write
        # uncomment next lines to print the response and check working correctly
        #print()
        #print("Made day folder in month folder")
        #print()
        return CheckFolderYmd


# =============================================================================
#
# Set up file headers for the different txt files being read into code
#
# =============================================================================

# Set file headers for data file structure
EventsFieldNames  = ['EventMax', 'Flux', 'EventStart', 'EventEnd','Class','Satellite']
SunRiseFieldNames = ['SunRiseTime', 'Location']
SunSetFieldNames  = ['SunRiseTime', 'Location']
XrayFieldNames    = ['XrayFluxTime', 'Satellite', 'SoftXrayFlux', 'SoftXrayEnergy', 'HardXrayFlux', 'HardXrayEnergy']
AerialFieldNames  = ['AerialTime', 'AerialValue']

# =============================================================================
#
# Set up paths to different data sets
#
# note this is going to access and store data for "yesterday"
# so using date now - timedelta(1)
#
# =============================================================================

# Set start path for xray data file structure
EventsPath = "/home/pi/VLF/data/NOAAxrayFlares/primary/"
SunRisePath = "/home/pi/VLF/data/SunRise/"
SunSetPath = "/home/pi/VLF/data/SunSet/"
XrayPath = "/home/pi/VLF/data/NOAAxrays/primary/"
AerialPath = "/home/pi/VLF/data/Aerial/"
EventPlotDataPath = "/home/pi/VLF/data/EventPlotDataDHO/"
Path = "/home/pi/VLF/data/"

# =============================================================================
#
# Events path
#
# output should be
#
# /home/pi/VLF/data/EventsG16/year/year-month/year-month-day.txt
# /home/pi/VLF/data/EventsG16/yyyy/yyyy-mm/yyyy-mm-dd.txt
#
# =============================================================================
# EventsPath add year folder
#EventsPathNameY = EventsPath + datetime.strftime(datetime.now() - timedelta(1), '%Y')
#print("Value of variable (EventsPathNameY): ",EventsPathNameY)
# Event path add month folder
#EventsPathNameYm = EventsPathNameY + "/" + datetime.strftime(datetime.now() - timedelta(1), '%Y-%m')
#print("Value of variable (EventsPathNameYm): ",EventsPathNameYm)
# Event path get txt file name
#EventsFileNameYmd = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d') + ".txt"
#print("Value of variable (EventsFileNameYmd): ",EventsFileNameYmd)
# Events path put it all together
#EventsPathFileNameYmd = EventsPathNameYm + "/" + EventsFileNameYmd
#print("Value of variable (EventsPathFileNameYmd): ",EventsPathFileNameYmd)

# Set start path for Event data file structure
# uncomment next lines to print the response
#print()
#print("Value of variable (EventsPath): ",EventsPath)
#print("Data type of variable (EventsPath): ",type(EventsPath))
#print()

Path=EventsPath
# Add year variable to path for Magnet data file structure
EventsPathNameY = GetPathnameYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (EventsPathNameY): ",EventsPathNameY)
#print("Data type of variable (EventsPathNameY): ",type(EventsPathNameY))
#print()

PathNameY=EventsPathNameY
# Add yearmonth variable to path for Events data file structure
EventsPathNameYm = GetPathnameYearMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (EventsPathNameYm): ",EventsPathNameYm)
#print("Data type of variable (EventsPathNameYm): ",type(EventsPathNameYm))
#print()

PathNameYm=EventsPathNameYm
# Make filemane of txt file to write Events data to
EventsFileNameYmd = GetFilenameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (EventsFileNameYmd): ",EventsFileNameYmd)
#print("Data type of variable (EventsFileNameYmd): ",type(EventsFileNameYmd))
#print()

# check full path and filename for writing Events data to
EventsPathFileNameYmd = EventsPathNameYm + "/" + EventsFileNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (EventsPathFileNameYmd): ",EventsPathFileNameYmd)
#print("Data type of variable (EventsPathFileNameYmd): ",type(EventsPathFileNameYmd))
#print()


# =============================================================================
#
# SunRise path
#
# output should be
#
# /home/pi/VLF/data/SunRise/year/year-month/year-month-day.txt
# /home/pi/VLF/data/SunRise/yyyy/yyyy-mm/yyyy-mm-dd.txt
#
# =============================================================================
# SunRisePath add year folder
#SunRisePathNameY = SunRisePath + datetime.strftime(datetime.now() - timedelta(1), '%Y')
#print("Value of variable (SunRisePathNameY): ",SunRisePathNameY)
# SunRisePath add month folder
#SunRisePathNameYm = SunRisePathNameY + "/" + datetime.strftime(datetime.now() - timedelta(1), '%Y-%m')
#print("Value of variable (SunRisePathNameYm): ",SunRisePathNameYm)
# SunRisePath get txt file name
#SunRiseFileNameYmd = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d') + ".txt"
#print("Value of variable (SunRiseFileNameYmd): ",SunRiseFileNameYmd)
# SunRise path put it all together
#SunRisePathFileNameYmd = SunRisePathNameYm + "/" + SunRiseFileNameYmd
#print("Value of variable (SunRisePathFileNameYmd): ",SunRisePathFileNameYmd)

Path=SunRisePath
# Add year variable to path for SunRise data file structure
SunRisePathNameY = GetPathnameYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (SunRisePathNameY): ",SunRisePathNameY)
#print("Data type of variable (SunRisePathNameY): ",type(SunRisePathNameY))
#print()

PathNameY=SunRisePathNameY
# Add yearmonth variable to path for SunRise data file structure
SunRisePathNameYm = GetPathnameYearMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (SunRisePathNameYm): ",SunRisePathNameYm)
#print("Data type of variable (SunRisePathNameYm): ",type(SunRisePathNameYm))
#print()

PathNameYm=SunRisePathNameYm
# Make filemane of txt file to write SunRise data to
SunRiseFileNameYmd = GetFilenameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (SunRiseFileNameYmd): ",SunRiseFileNameYmd)
#print("Data type of variable (SunRiseFileNameYmd): ",type(SunRiseFileNameYmd))
#print()

# check full path and filename for writing SunRise data to
SunRisePathFileNameYmd = SunRisePathNameYm + "/" + SunRiseFileNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (SunRisePathFileNameYmd): ",SunRisePathFileNameYmd)
#print("Data type of variable (SunRisePathFileNameYmd): ",type(SunRisePathFileNameYmd))
#print()


# =============================================================================
#
# SunSet path
#
# output should be
#
# /home/pi/VLF/data/SunSet/year/year-month/year-month-day.txt
# /home/pi/VLF/data/SunSet/yyyy/yyyy-mm/yyyy-mm-dd.txt
#
# =============================================================================
# SunSetPath add year folder
#SunSetPathNameY = SunSetPath + datetime.strftime(datetime.now() - timedelta(1), '%Y')
#print("Value of variable (SunSetPathNameY): ",SunSetPathNameY)
# SunSetPath add month folder
#SunSetPathNameYm = SunSetPathNameY + "/" + datetime.strftime(datetime.now() - timedelta(1), '%Y-%m')
#print("Value of variable (SunSetPathNameYm): ",SunSetPathNameYm)
# SunSetPath get txt file name
#SunSetFileNameYmd = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d') + ".txt"
#print("Value of variable (SunSetFileNameYmd): ",SunSetFileNameYmd)
# SunSet path put it all together
#SunSetPathFileNameYmd = SunSetPathNameYm + "/" + SunSetFileNameYmd
#print("Value of variable (SunSetPathFileNameYmd): ",SunSetPathFileNameYmd)

Path=SunSetPath
# Add year variable to path for SunSet data file structure
SunSetPathNameY = GetPathnameYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (SunSetPathNameY): ",SunSetPathNameY)
#print("Data type of variable (SunSetPathNameY): ",type(SunSetPathNameY))
#print()

PathNameY=SunSetPathNameY
# Add yearmonth variable to path for SunSet data file structure
SunSetPathNameYm = GetPathnameYearMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (SunSetPathNameYm): ",SunSetPathNameYm)
#print("Data type of variable (SunSetPathNameYm): ",type(SunSetPathNameYm))
#print()

PathNameYm=SunSetPathNameYm
# Make filemane of txt file to write SunSet data to
SunSetFileNameYmd = GetFilenameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (SunSetFileNameYmd): ",SunSetFileNameYmd)
#print("Data type of variable (SunSetFileNameYmd): ",type(SunSetFileNameYmd))
#print()

# check full path and filename for writing SunSet data to
SunSetPathFileNameYmd = SunSetPathNameYm + "/" + SunSetFileNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (SunSetPathFileNameYmd): ",SunSetPathFileNameYmd)
#print("Data type of variable (SunSetPathFileNameYmd): ",type(SunSetPathFileNameYmd))
#print()


# =============================================================================
#
# Aerial path
#
# output should be
#
# /home/pi/VLF/data/Aerial/year/year-month/year-month-day.txt
# /home/pi/VLF/data/Aerial/yyyy/yyyy-mm/yyyy-mm-dd.txt
#
# =============================================================================
# AerialPath add year folder
#AerialPathNameY = AerialPath + datetime.strftime(datetime.now() - timedelta(1), '%Y')
#print("Value of variable (AerialPathNameY): ",AerialPathNameY)
# AerialPath path add month folder
#AerialPathNameYm = AerialPathNameY + "/" + datetime.strftime(datetime.now() - timedelta(1), '%Y-%m')
#print("Value of variable (AerialPathNameYm): ",AerialPathNameYm)
# AerialPath path get txt file name
#AerialFileNameYmd = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d') + ".txt"
#print("Value of variable (AerialFileNameYmd): ",AerialFileNameYmd)
# Aerial path put it all together
#AerialPathFileNameYmd = AerialPathNameYm + "/" + AerialFileNameYmd
#print("Value of variable (AerialPathFileNameYmd): ",AerialPathFileNameYmd)

Path=AerialPath
# Add year variable to path for Aerial data file structure
AerialPathNameY = GetPathnameYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (AerialPathNameY): ",AerialPathNameY)
#print("Data type of variable (AerialPathNameY): ",type(AerialPathNameY))
#print()

PathNameY=AerialPathNameY
# Add yearmonth variable to path for Aerial data file structure
AerialPathNameYm = GetPathnameYearMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (AerialPathNameYm): ",AerialPathNameYm)
#print("Data type of variable (AerialPathNameYm): ",type(AerialPathNameYm))
#print()

PathNameYm=AerialPathNameYm
# Make filemane of txt file to write Aerial data to
AerialFileNameYmd = GetFilenameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (AerialFileNameYmd): ",AerialFileNameYmd)
#print("Data type of variable (AerialFileNameYmd): ",type(AerialFileNameYmd))
#print()

# check full path and filename for writing Aerial data to
AerialPathFileNameYmd = AerialPathNameYm + "/" + AerialFileNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (AerialPathFileNameYmd): ",AerialPathFileNameYmd)
#print("Data type of variable (AerialPathFileNameYmd): ",type(AerialPathFileNameYmd))
#print()


# =============================================================================
#
# xray path
#
# output should be
#
# /home/pi/VLF/data/XrayG16/year/year-month/year-month-day.txt
# /home/pi/VLF/data/XrayG16/yyyy/yyyy-mm/yyyy-mm-dd.txt
#
# =============================================================================
# XrayPath add year folder
#XrayPathNameY = XrayPath + datetime.strftime(datetime.now() - timedelta(1), '%Y')
#print('Value of variable (xrayPathNameY): ',xrayPathNameY)
# XrayPath path add month folder
#XrayPathNameYm = XrayPathNameY + '/' + datetime.strftime(datetime.now() - timedelta(1), '%Y-%m')
#print('Value of variable (XrayPathNameYm): ',XrayPathNameYm)
# XrayPath path get txt file name
#XrayFileNameYmd = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d') + '.txt'
#print('Value of variable (XrayFileNameYmd): ',XrayFileNameYmd)
# xray path put it all together
#XrayPathFileNameYmd = XrayPathNameYm + '/' + XrayFileNameYmd
#print('Value of variable (XrayPathFileNameYmd): ',XrayPathFileNameYmd)

Path=XrayPath
# Add year variable to path for Xray data file structure
XrayPathNameY = GetPathnameYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (XrayPathNameY): ",XrayPathNameY)
#print("Data type of variable (XrayPathNameY): ",type(XrayPathNameY))
#print()

PathNameY=XrayPathNameY
# Add yearmonth variable to path for Xray data file structure
XrayPathNameYm = GetPathnameYearMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (XrayPathNameYm): ",XrayPathNameYm)
#print("Data type of variable (XrayPathNameYm): ",type(XrayPathNameYm))
#print()

PathNameYm=XrayPathNameYm
# Make filemane of txt file to write Xray data to
XrayFileNameYmd = GetFilenameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (XrayFileNameYmd): ",XrayFileNameYmd)
#print("Data type of variable (XrayFileNameYmd): ",type(XrayFileNameYmd))
#print()

# check full path and filename for writing Xray data to
XrayPathFileNameYmd = XrayPathNameYm + "/" + XrayFileNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (XrayPathFileNameYmd): ",XrayPathFileNameYmd)
#print("Data type of variable (XrayPathFileNameYmd): ",type(XrayPathFileNameYmd))
#print()


# =============================================================================
#
# Event Plot Data path
#
# output should be
#
# /home/pi/VLF/data/EventPlotData23400/year/year-month/year-month-day_Event_No.txt
# /home/pi/VLF/data/EventPlotData23400/yyyy/yyyy-mm/yyyy-mm-dd_Exx.txt
#
# =============================================================================
# EventPlotData path get txt file name
#EventPlotDataYmd = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d') + '.txt'
#print('Value of variable (EventPlotDataYmd): ',EventPlotDataYmd)
# EventPlotData path add event number put it all together
#XrayPathFileNameYmd = XrayPathNameYm + '/' + XrayFileNameYmd
#print('Value of variable (XrayPathFileNameYmd): ',XrayPathFileNameYmd)

Path=EventPlotDataPath
# Add year variable to path for EventPlotData data file structure
EventPlotDataPathNameY = GetPathnameYear()
# uncomment next lines to print the response
#print()
#print("Value of variable (EventPlotDataPathNameY): ",EventPlotDataPathNameY)
#print("Data type of variable (EventPlotDataPathNameY): ",type(EventPlotDataPathNameY))
#print()

PathNameY=EventPlotDataPathNameY
# Add yearmonth variable to path for EventPlotData data file structure
EventPlotDataPathNameYm = GetPathnameYearMonth()
# uncomment next lines to print the response
#print()
#print("Value of variable (EventPlotDataPathNameYm): ",EventPlotDataPathNameYm)
#print("Data type of variable (EventPlotDataPathNameYm): ",type(EventPlotDataPathNameYm))
#print()

PathNameYm=EventPlotDataPathNameYm
# Add yearmonth variable to path for EventPlotData data file structure
EventPlotDataPathNameYmd = GetPathnameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (EventPlotDataPathNameYmd): ",EventPlotDataPathNameYmd)
#print("Data type of variable (EventPlotDataPathNameYmd): ",type(EventPlotDataPathNameYmd))
#print()

PathNameYm=EventPlotDataPathNameYm
# Make filemane of txt file to write EventPlotData data to
EventPlotDataFileNameYmd = GetFilenameYearMonthDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (EventPlotDataFileNameYmd): ",EventPlotDataFileNameYmd)
#print("Data type of variable (EventPlotDataFileNameYmd): ",type(EventPlotDataFileNameYmd))
#print()

# check full path and filename for writing EventPlotData data to
#EventPlotDataPathFileNameYmd = EventPlotDataPathNameYm + "/" + EventPlotDataFileNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (EventPlotDataPathFileNameYmd): ",EventPlotDataPathFileNameYmd)
#print("Data type of variable (EventPlotDataPathFileNameYmd): ",type(EventPlotDataPathFileNameYmd))
#print()

# Year folder needs creating??
folderY = EventPlotDataPathNameY
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

# Month folder needs creating in year folder??
folderYm = EventPlotDataPathNameYm
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

# Day folder needs creating in month folder??
folderYmd = EventPlotDataPathNameYmd
# uncomment next lines to print the response
#print()
#print("Value of variable (folderYmd): ",folderYmd)
#print("Data type of variable (folderYmd): ",type(folderYmd))
#print()
folderYmd = CheckFolderDay()
# uncomment next lines to print the response
#print()
#print("Value of variable (folderYmd) after: ",folderYmd)
#print("Data type of variable (folderYmd): ",type(folderYmd))
#print()



# =============================================================================
#
# Paths set up and checked that they have correct format 
# and date of files relates to yesterday
#
# =============================================================================

# =============================================================================
#
# Now get sunrise and sunset data to be used to see if event can be seen
#
# =============================================================================

# =============================================================================
#
# Start with sunrise data for yesterday
#
# get as string variable and datetime variable
# 
# =============================================================================
#get SunRise data ************
file = open(SunRisePathFileNameYmd,'r')
SunRiseData = file.read()
file.close()
      
# check data from file has been read correctly
#print('Get sunrise data...')
#print ('SunRiseData: ',SunRiseData)
#print ('SunRiseData (type): ',type(SunRiseData))
        
# get first part of data file
SunRiseStr = SunRiseData.split(',')[0]
#print ('SunRiseStr : ',SunRiseStr+'UTC')
#print ('SunRiseStr (type): ',type(SunRiseStr))

# convert string to datetime.datetime format
SunRiseDatetime = datetime.strptime(SunRiseStr,"%Y-%m-%d %H:%M:%S")
#print('Sun rises at : ',SunRiseDatetime,"UTC")
#print('SunRiseDatetime type : ',type(SunRiseDatetime))

# =============================================================================
#
# Now get sunset data for yesterday
#
# get as string variable and datetime variable
# 
# =============================================================================

#
#get civilEnd data
file = open(SunSetPathFileNameYmd,'r')
SunSetData = file.read()
file.close()
        
# check data from file has been read correctly
#print('Get sun set...')
#print ('SunSetData: ',SunSetData)
#print ('SunSetData (type): ',type(SunSetData))
        
# get first part of data file
SunSetStr = SunSetData.split(',')[0]
#print ('SunSetStr   : ',SunSetStr+'UTC')
#print ('SunSetStr (type): ',type(SunSetStr))

# convert string to datetime.datetime format
SunSetDatetime = datetime.strptime(SunSetStr,"%Y-%m-%d %H:%M:%S")
#print('Sun sets at  : ',SunSetDatetime,"UTC")
#print('SunSetDatetime type : ',type(SunSetDatetime))

# =============================================================================
#
# Got both sunrise and sunset data
#
# variable names:
#
#      SunRiseStr   = yyyy-mm-dd hh:mm:ss
#      SunSetStr    = yyyy-mm-dd hh:mm:ss
# 
# =============================================================================

# ==========================================================================================
#
# Couple of routines to get todays date and yesterdays date
#
# not used ????
# 
# ==========================================================================================

# get todays date and yesterdays date
#TodayString = datetime.strftime(datetime.now(), '%Y-%m-%d')
#print('Date now         : ',TodayString)
#print(type(TodayString))
# convert string to datetime.datetime format
#TodatDatetime = datetime.strptime(TodayString,"%Y-%m-%d")
#print('Date today : ',TodatDatetime)
#print('TodatDatetime type : ',type(TodatDatetime))

#YesterdayString = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
#print('Date yesterday   : ',YesterdayString)
#print(type(YesterdayString))
# convert string to datetime.datetime format
#YesterdayDatetime = datetime.strptime(YesterdayString,"%Y-%m-%d")
#print('Yesterday : ',YesterdayDatetime)
#print('YesterdayDatetime type : ',type(YesterdayDatetime))

# ==========================================================================================
#
# Main program
#
#     Idea is to get event data and then sort into different events that could have
#     occured after sun rise and before sun set for my VLF receiver
#     Need to think about downtime for VLF each day as well
# 
# ==========================================================================================

# ==========================================================================================
#
# simple routine to get number of lines in Events file
# Can then be used for looping in rest of code
# line.strip('\n') removes '\n' from end of line
#
# variables
#
# EventLineCount = number of events for yesterday
# 
# ==========================================================================================

EventsFile = open(EventsPathFileNameYmd,'r')
EventsNoEmptyLines=[line.strip('\n') for line in EventsFile if line !='\n']
EventsLineCount = len(EventsNoEmptyLines)
EventsFile.close()
print('Number of potential events yesterday :',EventsLineCount)
#print("File type of variable (EventsLineCount) :",type(EventsLineCount))


# Simple code to print each line
#count = 0
#with open('/home/pi/VLF/data/Events/2022/2022-05/2022-05-20.txt','r') as file:
#    for line in file:
#        count += 1
#        print('Line{}: {}'.format(count, line.rstrip()))


# Loop code to print each line from LineCount above
#with open(FileName,'r') as file:
    #Lines = file.readlines()
#    csv_reader = csv.reader(FileName,EventsFieldNames)
#    next(csv_reader)
#    for line in csv_reader:
#        print(file'Flux of event {line['Class']} is {line['Flux']} W')
#    for line in Lines:
#        #print(LineCount)
#        print('Line{}: {}'.format(LineCount, line.rstrip()))
#        LineCount -= 1

# ==========================================================================================
#
# routine to get start of event and end of event
# and add hour before and hour after event to set up parameters
# to plot event
#
# Will save these event to txt file for be processed by gnuplot
#
# ==========================================================================================

# using csv.DictReader
EventsFile = open(EventsPathFileNameYmd,'r')
EventsCSV_reader = csv.DictReader(EventsFile,EventsFieldNames)

PlotStartNumber = 0
PlotEndNumber = 0
EventNumber = 0

for EventLine in EventsCSV_reader:
    # Start of event time
    #print('The event maximum flux was : ' + EventLine['Flux'] + ' W/m^2')
    #print('The event started as : ' , EventLine['EventStart'])
    #print('Data type : ' , type(EventLine['EventStart'])) 
    EventDateTimeSting = EventLine['EventStart']
    #EventDate = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S").date()
    #print(EventDate)
    #print(type(EventDate))
    #EventTime = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S").time()
    #print(EventTime)
    #print(type(EventTime))
    EventDateTimeStart = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S")
    EventTimeStart = datetime.strftime(EventDateTimeStart,"%H:%M")
    #print('The start of the event was at : ',EventDateTimeStart)
    #print(type(EventDateTimeStart))
    PlotStart = EventDateTimeStart - timedelta(minutes=30)
    #print('The event plot starts at : ',PlotStart)
    #print(type(PlotStart))
    
    # Peak of event time
    EventDateTimeSting = EventLine['EventMax']
    #convert str to datetime.datetime format
    #EventDate = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S").date()
    #print(EventDate)
    #print(type(EventDate))
    #EventTime = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S").time()
    #print(EventTime)
    #print(type(EventTime))
    EventDateTimePeak = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S")
    EventTimePeak = datetime.strftime(EventDateTimePeak,"%H:%M")
    #print('The maximum of the event was at : ',EventDateTimePeak)
    #print(type(EventDateTimePeak))
    
    # End of event time
    EventDateTimeSting = EventLine['EventEnd']
    #convert str to datetime.datetime format
    #EventDate = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S").date()
    #print(EventDate)
    #print(type(EventDate))
    #EventTime = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S").time()
    #print(EventTime)
    #print(type(EventTime))
    EventDateTimeEnd = datetime.strptime(EventDateTimeSting,"%Y-%m-%d %H:%M:%S")
    EventTimeEnd = datetime.strftime(EventDateTimeEnd,"%H:%M")
    #print('The end of the event was at : ',EventDateTimeEnd)
    #print(type(EventDateTimeEnd))
    PlotEnd = EventDateTimeEnd + timedelta(minutes=30)
    #print('The event plot ends at : ',PlotEnd)
    #print(type(PlotEnd))

    # Class of event
    EventTimeClass = EventLine['Class']
    #print('The event class was : ',EventDateTimeClass)
    #print(type(EventDateTimeClass))
    
    # Output print test
    #print('Start plot at:',PlotStart,'and end plot at:',PlotEnd, 'for event')
    
    # now have if loop to see if the data is within sunrise to sunset times
    # start with event after sunrise
    if PlotStart >= SunRiseDatetime:
        PlotStartNumber = PlotStartNumber +1
        #print(PlotStartNumber)
        #print('SunRise time :',SunRiseDatetime)
        #print('PlotStart time :',PlotStart)
        #print('Start plot at:',PlotStart,'and end plot at:',PlotEnd, 'for event')
        #print('Event after sunrise, can evaluate data')
        
        # now try event before sunset
        if PlotEnd <= SunSetDatetime:
            PlotEndNumber = PlotEndNumber +1
            #print(PlotEndNumber)
            EventNumber = PlotEndNumber
            #print(EventNumber)
            #print('SunSet time :',SunSetDatetime)
            #print('PlotEnd time :',PlotEnd)
            print('Event between SunRise and SunSet :', EventNumber)
            print('Start plot at:',PlotStart,'and end plot at:',PlotEnd, 'for event', EventNumber)
            #print('Event before sunset, can evaluate data')
            
            # open xray data file and get data between start and end times of plot
            XrayFile = open(XrayPathFileNameYmd,'r')
            XrayNoEmptyLines=[line.strip('\n') for line in XrayFile if line !='\n']
            XrayLineCount = len(XrayNoEmptyLines)
            XrayFile.close()
            #print('Number of xray data yesterday :',XrayLineCount)
                        
            # check read data file in
            #print('Xray data for yesterday :',XrayLineCount)
            #print("File type of variable (XrayLineCount) :",type(XrayLineCount))
            
            # using csv.DictReader
            XrayFile = open(XrayPathFileNameYmd,'r')
            XrayCSV_reader = csv.DictReader(XrayFile,XrayFieldNames)
            
            for XrayLine in XrayCSV_reader:
                #print('The flux was : ', XrayLine['HardXrayFlux'] , ' W/m^2')
                
                # try to get xray data after start of plot
                # convert string to datetime.datetime format
                XrayDatetime = datetime.strptime(XrayLine['XrayFluxTime'],"%Y-%m-%d %H:%M:%S")
                #print('XrayDatetime : ',XrayDatetime)
                #print('XrayDatetime type : ',type(XrayDatetime))

                if XrayDatetime >= PlotStart:
                    #print('The flux was : ', XrayLine['HardXrayFlux'] , ' W/m^2')
                    
                    # Now only get data up to end of plot
                    if XrayDatetime <= PlotEnd:
                        #print('The flux was : ', XrayLine['HardXrayFlux'] , ' W/m^2 at ', XrayLine['XrayFluxTime'])
            
                        # close open XrayFile
                        #XrayFile.close()
                        
                        # write data to file
                        FlareData= open(EventPlotDataPathNameYmd + "/" + "Xray_Event_" + str(EventNumber) + "_" + EventPlotDataFileNameYmd,'a+')
                        FlareData.write(str(XrayDatetime))       # Data date
                        FlareData.write(",")                     # , separator
                        FlareData.write(str(XrayLine['HardXrayFlux']))       # X-ray flux data value
                        FlareData.write("\n")                    # new line
                        FlareData.close()


            # open aerial data file and get data between start and end times of plot
            AerialFile = open(AerialPathFileNameYmd,'r')
            AerialNoEmptyLines=[line.strip('\n') for line in AerialFile if line !='\n']
            AerialLineCount = len(AerialNoEmptyLines)
            AerialFile.close()
            #print('Number of xray data yesterday :',XrayLineCount)
                        
            # check read data file in
            #print('Aerial data for yesterday :',AerialLineCount)
            #print("File type of variable (AerialLineCount) :",type(AerialLineCount))
            
            # using csv.DictReader
            AerialFile = open(AerialPathFileNameYmd,'r')
            AerialCSV_reader = csv.DictReader(AerialFile,AerialFieldNames)
            
            for AerialLine in AerialCSV_reader:
                #print('The VLF was : ', AerialLine['AerialValue'] , ' V')
                
                # try to get  data after start of plot
                # convert string to datetime.datetime format
                AerialDatetime = datetime.strptime(AerialLine['AerialTime'],"%Y-%m-%d %H:%M:%S")
                #print('AerialDatetime : ',AerialDatetime)
                #print('AerialDatetime type : ',type(AerialDatetime))

                if AerialDatetime >= PlotStart:
                    #print('The VLF was : ', AerialLine['AerialValue'] , ' V')
                    
                    # Now only get data up to end of plot
                    if AerialDatetime <= PlotEnd:
                        #print('The VLF was : ', AerialLine['AerialValue'] , ' V at ', AerialLine['AerialTime'])

                        # write data to file
                        FlareData= open(EventPlotDataPathNameYmd +"/" + "VLF_Event_" + str(EventNumber) + "_" + EventPlotDataFileNameYmd,'a+')
                        FlareData.write(str(AerialDatetime))       # Data date
                        FlareData.write(",")                     # , separator
                        FlareData.write(str(AerialLine['AerialValue']))       # X-ray flux data value
                        FlareData.write("\n")                    # new line
                        FlareData.close()


            # close open AerialFile
            AerialFile.close()
            
            # close open XrayFile
            XrayFile.close()

            # write Event data to file
            EventData= open(EventPlotDataPathNameYmd + "/" + "Data_Event_" + str(EventNumber) + "_" + EventPlotDataFileNameYmd,'a+')
            EventData.write(str(EventTimeStart))       # Start of event date time
            EventData.write(",")                           # , separator
            EventData.write(str(EventTimePeak))        # Peak of event date time
            EventData.write(",")                           # , separator
            EventData.write(str(EventTimeEnd))         # End of event date time
            EventData.write(",")                           # , separator
            EventData.write(str(EventTimeClass))       # Class of event
            EventData.write(",")                           # , separator
            EventData.write(str(EventTimeClass)+" event start")                         # " " separator
            EventData.write(",")                           # , separator
            EventData.write(str(EventDateTimeStart))       # Start of event date time
            EventData.write(",")                           # , separator
            EventData.write(str(EventTimeClass)+" event maximum")                         # " " separator
            EventData.write(",")                           # , separator
            EventData.write(str(EventDateTimePeak))        # Peak of event date time
            EventData.write(",")                           # , separator
            EventData.write(str(EventTimeClass)+" event end")                         # " " separator
            EventData.write(",")                           # , separator
            EventData.write(str(EventDateTimeEnd))         # End of event date time
            EventData.write("\n")                          # new line
            EventData.close()


            
# check count is working and how many plots will be done
#print("Number of start events to plot :",PlotStartNumber)
#print("Number of end events to plot :",PlotEndNumber)

# write Event data to file
NoData= open(EventPlotDataPathNameYmd + "/" + "NumberOfEvents_" + EventPlotDataFileNameYmd,'a+')
NoData.write(str(PlotEndNumber))            # Number of events today
NoData.write(",")                           # , separator
NoData.write(str(PlotStartNumber))          # Number of possible events today
NoData.write("\n")                          # new line
NoData.close()


# close open EventsFile
EventsFile.close()

# ==========================================================================================
#
# Having got start and end times for the event
# now get the xray flux data between these times
#
# Will save these event to txt file for be processed by gnuplot
#
# ==========================================================================================

# ==========================================================================================
#
# END of program
#
# ==========================================================================================
#
# - gets data from sunrise, sunset, xray, aerial and events for yesterday
#
# - create data file to store event specific data into
# - checks that there is a year folder for events plot data - if not create one
# - checks that there is a month folder for events plot data - if not creates one
# - checks that there is a day folder for events plot data - if not creates one
# - creates file name based on year and then year month
#
# - extracts data from aerial and xray for 1 hour before event start
# - to one hour after event ends
#
# - writes data to file (txt) for xray and aerial data
# - format: date (YYYY-MM-DD) time (hh:mm:00), He magnetic flux (number), Hp magnetic flux (number), Hn magnetic flux (number), total magnetic flux (number), arcjet_flag (boolean)
#
#
# - runs via CRON each day at 2.20AM
#   crontab entry  "20 2 * * * /usr/bin/python3 /home/pi/VLF/scripts/CreateDataEventsPlots23400.py> /home/pi/VLF/LogFiles/cron-Magnet.log 2>&1"
#
# ==========================================================================================