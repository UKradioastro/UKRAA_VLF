#!/usr/bin/env python3

# ==========================================================================================
#
# INFORMATION
#
# ==========================================================================================

# program to get the instrument sources for GOES 16 and 18
# data available as 
# events data : https://services.swpc.noaa.gov/json/goes/instrument-sources.json
#
# data has format
#
#     electron       :                       : primary and secondary data source
#         primary    : format = "XX"         : GOES satellite number
#         secondary  : format = "XX"         : GOES satellite number
#     protons        :                       : primary and secondary data source
#         primary    : format = "XX"         : GOES satellite number
#         secondary  : format = "XX"         : GOES satellite number
#     magnetometers  :                       : primary and secondary data source
#         primary    : format = "XX"         : GOES satellite number
#         secondary  : format = "XX"         : GOES satellite number
#     xrays          :                       : primary and secondary data source 
#         primary    : format = "XX"         : GOES satellite number
#         secondary  : format = "XX"         : GOES satellite number
#
# data is recorded for primary and secondary data streamsevery event


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
import configparser

config = configparser.ConfigParser()
config.read('/home/pi/VLF/data/vlfdata.ini')
#print(config.sections())

# ==========================================================================================
#
# Prinary and secondary NOAA data file structure
#
# ==========================================================================================
#
# Path parameters for NOAA data file structure
#
# Path                  : /home/pi/VLF/data/DataNOAA

# Set path for NOAA data file structure
NOAAPathFileName = "/home/pi/VLF/data/DataNOAA.ini"
# uncomment next lines to print the response
#print()
#print("Value of variable (NOAAPathFileName): ",NOAAPathFileName)
#print("Data type of variable (NOAAPathFileName): ",type(NOAAPathFileName))
#print()


# ==========================================================================================
#
# Get NOAA events data from WWW
#
# ==========================================================================================
#
# Set up the parameters we want to pass to get data.
#
# Idea is to get instrument-sources JSON data
# and extract which satellite is the primary source and which the secondary source
# for electrons, protons, magnetometers and xrays
# and then store it to a .txt file.
#
# program to get the events data from NOAA
#
# data available as 
# events data : https://services.swpc.noaa.gov/json/goes/instrument-sources.json
#
# data has format
#
#     electron       :                       : primary and secondary data source
#         primary    : format = "XX"         : GOES satellite number
#         secondary  : format = "XX"         : GOES satellite number
#     protons        :                       : primary and secondary data source
#         primary    : format = "XX"         : GOES satellite number
#         secondary  : format = "XX"         : GOES satellite number
#     magnetometers  :                       : primary and secondary data source
#         primary    : format = "XX"         : GOES satellite number
#         secondary  : format = "XX"         : GOES satellite number
#     xrays          :                       : primary and secondary data source 
#         primary    : format = "XX"         : GOES satellite number
#         secondary  : format = "XX"         : GOES satellite number
#
# data is recorded for primary and secondary data streamsevery event


# Make a get request with the parameters.
#

# variables
# URL variable of Scraped data
# Events data from NOAA - used
AddressURL = "https://services.swpc.noaa.gov/json/goes/instrument-sources.json"

# Check if getting data
# uncomment next lines to print the response
# print message to log file to say started process
print('Getting NOAA instrument source data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))


response = requests.get(AddressURL, stream=True)

# pass this to variable for maniputation in program
#
# note used to save as temp file - now just processed in program
#

NOAAData=json.loads(response.text)
# Check json data variable got
# uncomment next lines to print the response
#print('Got NOAA instrument source data on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

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
# Extract data from JSON dictionary for electrons, protons, magnetometers and xrays
#
# Data variable used:
#     NOAAData = JSON dictionary
#
# Data variable created:
#
#     NOAAElectronsPrimary       = primary GOES electron data source        = format XX
#     NOAAElectronsSecondary     = secondary GOES electron data source      = format XX
#     NOAAProtonsPrimary         = primary GOES Protons data source         = format XX
#     NOAAProtonsSecondary       = secondary GOES Protons data source       = format XX
#     NOAAMagnetometersPrimary   = primary GOES Magnetometers data source   = format XX
#     NOAAMagnetometersSecondary = secondary GOES Magnetometers data source = format XX
#     NOAAXraysPrimary           = primary GOES Xrays data source           = format XX
#     NOAAXraysSecondary         = secondary GOES Xrays data source         = format XX
#


for NOAA in NOAAData:
    # Print the content of the response (the data the server returned)
    # uncomment next lines to print the response
    #print()
    #print("Variable content of NOAA['electrons']: ",NOAA['electrons'])
    #print("Variable content of NOAA['electrons primary']: ",NOAA['electrons']['primary'])
    #print("Variable content of NOAA['electrons secondary']: ",NOAA['electrons']['secondary'])
    #print()
    #print("Variable content of NOAA['protons']: ",NOAA['protons'])
    #print("Variable content of NOAA['protons primary']: ",NOAA['protons']['primary'])
    #print("Variable content of NOAA['protons secondary']: ",NOAA['protons']['secondary'])
    #print()
    #print("Variable content of NOAA['magnetometers']: ",NOAA['magnetometers'])
    #print("Variable content of NOAA['magnetometers primary']: ",NOAA['magnetometers']['primary'])
    #print("Variable content of NOAA['magnetometers secondary']: ",NOAA['magnetometers']['secondary'])
    #print()
    #print("Variable content of NOAA['xrays']: ",NOAA['xrays'])
    #print("Variable content of NOAA['xrays primary']: ",NOAA['xrays']['primary'])
    #print("Variable content of NOAA['xrays secondary']: ",NOAA['xrays']['secondary'])
    #print()
    
    #set up variable to write to file
    NOAAElectronsPrimary       = NOAA['electrons']['primary']
    NOAAElectronsSecondary     = NOAA['electrons']['secondary']
    NOAAProtonsPrimary         = NOAA['protons']['primary']
    NOAAProtonsSecondary       = NOAA['protons']['secondary']
    NOAAMagnetometersPrimary   = NOAA['magnetometers']['primary']
    NOAAMagnetometersSecondary = NOAA['magnetometers']['secondary']
    NOAAXraysPrimary           = NOAA['xrays']['primary']
    NOAAXraysSecondary         = NOAA['xrays']['secondary']
    #NOAAsuviPrimary            = NOAA['suvi']['primary']
    #NOAAsuviSecondary          = NOAA['suvi']['secondary']
    
    # ==========================================================================================
    #
    # Write data to path/file (text file)
    #
    # ==========================================================================================
    #
    # Variable list
    #
    #     NOAAPathFileName           = path and file name
    #
    #     NOAAElectronsPrimary       = primary GOES electron data source        = format XX
    #     NOAAElectronsSecondary     = secondary GOES electron data source      = format XX
    #     NOAAProtonsPrimary         = primary GOES Protons data source         = format XX
    #     NOAAProtonsSecondary       = secondary GOES Protons data source       = format XX
    #     NOAAMagnetometersPrimary   = primary GOES Magnetometers data source   = format XX
    #     NOAAMagnetometersSecondary = secondary GOES Magnetometers data source = format XX
    #     NOAAXraysPrimary           = primary GOES Xrays data source           = format XX
    #     NOAAXraysSecondary         = secondary GOES Xrays data source         = format XX
    #
            
    '''        
    #print("Start writing to file")
    NOAAData= open(NOAAPathFileName,'w')
    NOAAData.write("ElectronsPrimary")           # Primary electron GOES satellite
    NOAAData.write(",")                               # "," separator
    NOAAData.write(str(NOAAElectronsPrimary))         # Number of GOES satellite
    NOAAData.write("\n")                              # new line
    NOAAData.write("ElectronsSecondary")           # Secondary electron GOES satellite
    NOAAData.write(",")                                 # "," separator
    NOAAData.write(str(NOAAElectronsSecondary))         # Number of GOES satellite
    NOAAData.write("\n")                                # new line
    NOAAData.write("ProtonPrimary")             # Primary Protons GOES satellite
    NOAAData.write(",")                               # "," separator
    NOAAData.write(str(NOAAProtonsPrimary))           # Number of GOES satellite
    NOAAData.write("\n")                              # new line
    NOAAData.write("ProtonSecondary")             # Secondary Protons GOES satellite
    NOAAData.write(",")                                 # "," separator
    NOAAData.write(str(NOAAProtonsSecondary))           # Number of GOES satellite
    NOAAData.write("\n")                                # new line
    NOAAData.write("MagnetometerPrimary")           # Primary Magnetometers GOES satellite
    NOAAData.write(",")                                   # "," separator
    NOAAData.write(str(NOAAMagnetometersPrimary))         # Number of GOES satellite
    NOAAData.write("\n")                                  # new line
    NOAAData.write("MagnetometerSecondary")           # Secondary Magnetometers GOES satellite
    NOAAData.write(",")                                     # "," separator
    NOAAData.write(str(NOAAMagnetometersSecondary))         # Number of GOES satellite
    NOAAData.write("\n")                                    # new line
    NOAAData.write("XrayPrimary")               # Primary xrays GOES satellite
    NOAAData.write(",")                               # "," separator
    NOAAData.write(str(NOAAXraysPrimary))             # Number of GOES satellite
    NOAAData.write("\n")                              # new line
    NOAAData.write("XraySecondary")               # Secondary xrays GOES satellite
    NOAAData.write(",")                                 # "," separator
    NOAAData.write(str(NOAAXraysSecondary))             # Number of GOES satellite
    NOAAData.write("\n")                                # new line
    NOAAData.write("suviPrimary")               # Primary xrays GOES satellite
    NOAAData.write(",")                               # "," separator
    NOAAData.write(str(NOAAsuviPrimary))             # Number of GOES satellite
    NOAAData.write("\n")                              # new line
    NOAAData.write("suviSecondary")               # Secondary xrays GOES satellite
    NOAAData.write(",")                                 # "," separator
    NOAAData.write(str(NOAAsuviSecondary))             # Number of GOES satellite
    NOAAData.write("\n")                                # new line
    NOAAData.close()
    #print("End writing to file")
    '''
    
    config.set('NOAA_electrons', 'primary', str(NOAAElectronsPrimary))
    config.set('NOAA_electrons', 'secondary', str(NOAAElectronsSecondary))
    config.set('NOAA_protons', 'primary', str(NOAAProtonsPrimary))
    config.set('NOAA_protons', 'secondary', str(NOAAProtonsSecondary))
    config.set('NOAA_magnetometers', 'primary', str(NOAAMagnetometersPrimary))
    config.set('NOAA_magnetometers', 'secondary', str(NOAAMagnetometersSecondary))
    config.set('NOAA_xrays', 'primary', str(NOAAXraysPrimary))
    config.set('NOAA_xrays', 'secondary', str(NOAAXraysSecondary))
    #config.set('NOAA_suvi', 'primary', str(NOAAsuviPrimary))
    #config.set('NOAA_suvi', 'secondary', str(NOAAsuviSecondary))
    with open ('/home/pi/VLF/data/vlfdata.ini', 'w') as f:
        config.write(f)
            
            
#print message to log file to say completed process
print('Completed NOAA data source on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))


# ==========================================================================================
#
# END of program
#
# ==========================================================================================
#
# - scrapes events data from https://services.swpc.noaa.gov/json/goes/instrument-sources.json
# - extracts events for primary and secondary sources for electrons, protons, magnetometers and xrays 
# - writes data to file (txt)
# - path /home/pi/VLF/data/DataNOAA
#
# - runs via CRON each day at 1.30AM
#   crontab entry  "30 1 * * * /usr/bin/python3 /home/pi/VLF/scripts/GetDataNOAA.py> /home/pi/VLF/LogFiles/cron-dataNOAA.log 2>&1"
#
# ==========================================================================================