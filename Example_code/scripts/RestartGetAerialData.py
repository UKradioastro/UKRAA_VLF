#!/usr/bin/env python3

import psutil
from subprocess import Popen
from datetime import datetime

# check if DHO38 aerial "GetDataAerial.py" scripe is working - 23400Hz
for process in psutil.process_iter():
    if process.cmdline() == ['/usr/bin/python3', '/home/pi/VLF/scripts/GetDataAerial.py']:
        #print('GetDataAerial.py process found. Do nothing.',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))
        #PID_GetDataAerial = True
        # process.terminate()
        break
else:
    #print('Process not found: starting it.')
    print('Restarting GetDataAerial.py on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))
    Popen(['/usr/bin/python3', '/home/pi/VLF/scripts/GetDataAerial.py'])

# check if HWA aerial "GetDataAerial19600.py" scripe is working - 19600Hz
for process in psutil.process_iter():
    if process.cmdline() == ['/usr/bin/python3', '/home/pi/VLF/scripts/GetDataAerial19600.py']:
        #print('GetDataAerial19600.py process found. Do nothing.',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))
        #PID_GetDataAerial21750 = True
        # process.terminate()
        break
else:
    #print('Process not found: starting it.')
    print('Restarting GetDataAerial19600.py on',datetime.strftime(datetime.now(), '%Y-%m-%d'),'at',datetime.strftime(datetime.now(), '%H:%M:%S'))
    Popen(['/usr/bin/python3', '/home/pi/VLF/scripts/GetDataAerial19600.py'])