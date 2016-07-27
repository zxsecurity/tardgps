#!/usr/bin/env python3
# coding=utf-8

"""
tardgps.py is tool that will use GPS to move time backwards. The goal is to move time backwards for an NTPd server without it breaking. 

This tool makes use og bladgeGPS (https://github.com/osqzss/bladeGPS) to do the GPS work. You will need the brdc for the day ftp://cddis.gsfc.nasa.gov/gnss/data/daily/

command:
    tardgps.py
    
The configuration of the dates, times and brdc are in tardgps.cfg and the logging configuarion by logging.cfg

"""

import sys
import os
import configparser
import logging
import logging.config
import time
import threading
from datetime import datetime, timedelta
from gps3 import gps3


__author__ = 'Karit'
__copyright__ = 'Copyright 2016 Karit'
__license__ = 'MIT'
__version__ = '0.1'



#Get current time as start time
#Get the time you want to move to
#Get Location
#Get the negitive time step needed
#Boardcast the current time on GPS
#Wait until GPS has a fix and has the time
#Boardcast the current boardcast time -X minutes
#Wait until GPS has a fix and has the time
#loop
#When get required time keep boardcasting that

def run_blade(time):
    kill_boardcast()
    #./bladegps -e dave.16n -l 30.286502,120.032669,100 -t 2016/05/31,13:00:00
    bin_path = cfg.get('blade', 'bladegps_path')
    brdc_file = cfg.get('data', 'brdc')
    latitude = cfg.get('location', 'latitude')
    longitude = cfg.get('location', 'longitiude')
    altitude = cfg.get('location', 'altitude')
    time_formated = time.strftime('%Y/%m/%d,%H:%M:%S')
    command = '%s -e %s -l %s,%s,%s -t %s&' % (bin_path, brdc_file, latitude, longitude, altitude, time_formated)
    logger.info('Starting bldeGPS')
    logger.debug('Using the follow command line: %s' % (command))
    os.system(command)

def broadcast_gps(targetTime, groundhog):
    startTime = datetime.now()
    threading.Thread(target=run_blade(targetTime)).start()
    wait_for_gps_fix()
    currentGPSTime = get_gps_time()
    flag = False
    while True:        
        currentTime = datetime.now()
        runningTime = currentTime - startTime
        movingTargetTime = targetTime + runningTime
        window = cfg.getint('time', 'window')
        highMovingTargetTime = movingTargetTime + timedelta(seconds=window)
        lowMovingTargetTime = movingTargetTime - timedelta(seconds=window)
        previousGPSTime = currentGPSTime
        currentGPSTime = get_gps_time()
        if flag:
            # We have reached the target time and groundhog is off
            pass
        elif previousGPSTime == currentGPSTime:
            logger.debug('No new GPS fix. previousGPSTime == currentGPSTime. Sleeping 5 seconds.')
        else:
            logger.debug('Current GPS Time: %s. Low Moving Target Time: %s. High Moving Target Time: %s.' % (currentGPSTime, lowMovingTargetTime, highMovingTargetTime))
            if currentGPSTime >= lowMovingTargetTime:
                if currentGPSTime <= highMovingTargetTime:
                    if groundhog:
                        stabliseTime = cfg.getint('time', 'stabilise_time')
                        logger.debug('Sleeping for stabilise time of: %s' % (stabliseTime))
                        time.sleep(stabliseTime)
                        logger.info('Iteration Target Time reached')
                        return                     
                    else:
                        logger.info('Target Time reached. Will perform no more, time changes')               
                        flag = True   
        time.sleep(5)
   
def coordinate():
    wait_for_gps_fix()
    currentGPSTime = get_gps_time()
    targetTime = datetime.strptime(cfg.get('time', 'target'), '%Y-%m-%d %H:%M:%S')
    timeStep = cfg.getint('time', 'step')
    stabliseTime = cfg.getint('time', 'stabilise_time')
    groundhog = cfg.getboolean('time', 'groundhog')    
    while True:
        currentGPSTime = get_gps_time()
        newTime = currentGPSTime - timedelta(seconds=timeStep)
        if newTime < targetTime and not groundhog:
            logger.info('Moving time from %s to %s target time is %s' % (currentGPSTime, targetTime, targetTime))
            logger.info('Will stop time warping as groundhog is false')
            broadcast_gps(targetTime, False)
        elif newTime < targetTime and groundhog:
            logger.info('Moving time from %s to %s target time is %s' % (currentGPSTime, targetTime, targetTime))
            logger.info('Will keep time warping as groundhog is true')
            broadcast_gps(targetTime, True)
        else:        
            logger.info('Moving time from %s to %s target time is %s' % (currentGPSTime, newTime, targetTime))
            broadcast_gps(newTime, True) 
            
def wait_for_gps_fix():
    for new_data in gps_socket:
        if new_data:
            gps_fix.refresh(new_data)
            if gps_fix.TPV['mode'] != 'n/a' and gps_fix.TPV['mode'] >= 2:
                logger.debug('Got a GPS fix.')
                return
            else:
                logger.info('No GPS fix. Sleeping 5 seconds.')
                time.sleep(5)
            
def get_gps_time():
    for new_data in gps_socket:
        if new_data:
            gps_fix.refresh(new_data)
            if gps_fix.TPV['time'] != 'n/a':
                time = datetime.strptime(gps_fix.TPV['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                time = time.replace(tzinfo=None)
                return time        

def kill_boardcast():
    pids = get_pid('bladegps')
    for pid in pids:
        os.system('kill -9 %s' % (pid))
    
def get_pid(name):
    pids = []
    ps = os.popen("ps -ef | grep %s | grep -v grep" % (name)).read()
    lines = ps.splitlines()
    for line in lines:
        pids.append(line.split()[1])
    return pids

def connect_to_gpsd():
    """
    Connect to the GPSd deamons
    
    The configuartion for this is tardgps.cfg
    """
    logger.debug('Connecting to GPSd')
    host = cfg.get('gpsd', 'host')
    port = cfg.getint('gpsd', 'port')
    protocol = cfg.get('gpsd', 'protocol')
    global gps_socket
    global gps_fix
    try:
        gps_socket = gps3.GPSDSocket()
        gps_socket.connect(host, port)
        gps_socket.watch(gpsd_protocol=protocol)
        gps_fix = gps3.Fix()
    except:
        logger.error('Connection to gpsd at \'{0}\' on port \'{1}\' failed.'.format(cfg.get('gpsd', 'host'), cfg.getint('gpsd', 'port')))
        sys.exit(1)
    logger.debug('Connected to GPSd')
            
            
def shut_down():
    """
    Closes connections and threads
    """
    gps_socket.close()
    kill_boardcast()
    logger.debug('Closed connection to GPSd')
    print('Keyboard interrupt received\nTerminated by user\nGood Bye.\n')
    logger.info('Keyboard interrupt received. Terminated by user. Good Bye.')
    sys.exit(1)
            

def start_script():
    global cfg
    cfg = configparser.ConfigParser()
    cfg.read('tardgps.cfg')
    
    global logger
    logging.config.fileConfig('logging.cfg')
    logger = logging.getLogger(__name__)
    logger.info('Starting tardgps')

    connect_to_gpsd()

    
    try:
        pass
        coordinate()
    except KeyboardInterrupt:
        shut_down()
    except (OSError, IOError) as error:
        gps_socket.close()
        kill_boardcast()
        sys.stderr.write('\rError--> {}'.format(error))
        logger.error('Error--> {}'.format(error))
        sys.stderr.write('\rConnection to gpsd at \'{0}\' on port \'{1}\' failed.\n'.format(cfg.get('gpsd', 'host'), cfg.getint('gpsd', 'port')))
        logger.error('Connection to gpsd at \'{0}\' on port \'{1}\' failed.'.format(cfg.get('gpsd', 'host'), cfg.getint('gpsd', 'port')))
        sys.exit(1)

if __name__ == '__main__':
    start_script()
