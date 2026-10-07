#!/usr/bin/env python3

# ==========================================================================================
#
#  Import function
#
# ==========================================================================================

from datetime import datetime, timedelta
import configparser

config = configparser.ConfigParser()
config.read('/home/pi/VLF/data/vlfdata.ini')
#print(config.sections())

#print message to log file to say started process
print('Started updating calendar INI entries on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))

# ==========================================================================================
#
#  Use definitions
#
# ======================================================================

#today
# year folder - today
todayyearfolder = datetime.strftime(datetime.now(), '%Y')
#print('The variable (todayyearfolder) has value : ', todayyearfolder)
config.set('calender_today', 'year', str(todayyearfolder))

# year-month folder - today
todayyearmonthfolder = datetime.strftime(datetime.now(), '%Y-%m')
#print('The variable (todayyearmonthfolder) has value : ', todayyearmonthfolder)
config.set('calender_today', 'yearmonth', str(todayyearmonthfolder))


# year-month-today file - today
todayyearmonthdayfile = datetime.strftime(datetime.now(), '%Y-%m-%d')
#print('The variable (todayyearmonthdayfile) has value : ', todayyearmonthdayfile)
config.set('calender_today', 'yearmonthday', str(todayyearmonthdayfile))

# yesterday
# year folder - today
yesterdayyearfolder = datetime.strftime(datetime.now() - timedelta(1), '%Y')
#print('The variable (yesterdayyearfolder) has value : ', yesterdayyearfolder)
config.set('calender_yesterday', 'year', str(yesterdayyearfolder))

# year-month folder - today
yesterdayyearmonthfolder = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m')
#print('The variable (yesterdayyearmonthfolder) has value : ', yesterdayyearmonthfolder)
config.set('calender_yesterday', 'yearmonth', str(yesterdayyearmonthfolder))

# year-month-today file - today
yesterdayyearmonthdayfile = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
#print('The variable (yesterdayyearmonthdayfile) has value : ', yesterdayyearmonthdayfile)
config.set('calender_yesterday', 'yearmonthday', str(yesterdayyearmonthdayfile))

# tomorrow
# year folder - tomorrow
tomorrowyearfolder = datetime.strftime(datetime.now() + timedelta(1), '%Y')
#print('The variable (tomorrowyearfolder) has value : ', tomorrowyearfolder)
config.set('calender_tomorrow', 'year', str(tomorrowyearfolder))

# year-month folder - tomorrow
tomorrowyearmonthfolder = datetime.strftime(datetime.now() + timedelta(1), '%Y-%m')
#print('The variable (tomorrowyearmonthfolder) has value : ', tomorrowyearmonthfolder)
config.set('calender_tomorrow', 'yearmonth', str(tomorrowyearmonthfolder))

# year-month-today file - tomorrow
tomorrowyearmonthdayfile = datetime.strftime(datetime.now() + timedelta(1), '%Y-%m-%d')
#print('The variable (tomorrowyearmonthdayfile) has value : ', tomorrowyearmonthdayfile)
config.set('calender_tomorrow', 'yearmonthday', str(tomorrowyearmonthdayfile))

with open('/home/pi/VLF/data/vlfdata.ini', 'w') as configfile:
    config.write(configfile)

#print message to log file to say completed process
print('Completed updating calendar INI entries on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))
