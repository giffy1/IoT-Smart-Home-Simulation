# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 20:40:01 2017

@author: snoran

This test makes sure that the home system is working as expected.

"""

import device
from device import Device
import time
import numpy as np
import threading
from threading import Lock
import sys

if len(sys.argv) > 1:
    if sys.argv[1] == '-f':
        device.debug = False

print_lock = Lock()

# first set up the IoT system:
address = ('localhost', 8881)

motion_sensor = Device(address, 'sensor', 'motion')
motion_sensor.connect()

time.sleep(0.5)

door_sensor = Device(address, 'sensor', 'door')
door_sensor.connect()

time.sleep(0.5)

security_system = Device(address, 'device', 'security')
security_system.connect()

time.sleep(0.5)

beacon = Device(address, 'sensor', 'beacon')
beacon.connect()

time.sleep(2)

def close_door():
    """
    The door closes after some normally distributed delay. It cannot be guaranteed 
    that motion is detected before the door closes. Perhaps the person is carrying 
    in a bunch of groceries or the door automatically closes slowly via a spring. 
    Let's assume this is normally distributed
    """
    delay = 0
    while delay < 0.5: # arbitrary min time for door delay (certainly can't be negative)
        delay = np.random.normal(2, 2)
    time.sleep(delay)
    with print_lock:
        print "Door closed"
    door_sensor._set_state(0) # indicates open
    door_sensor.report_state()
    
def simulate_person_leaving():
    """
    Simulates the event that a person leaves the house. In this case, the motion 
    sensor will be triggered and some normally distributed time later, the door 
    is opened, then it will close.
    """
    with print_lock:
        print "Simulating person leaving..."
        print "Motion detected"
    motion_sensor._set_state(1) # motion detected
    motion_sensor.report_state()
    
    delay = 1 # delay after motion before no motion detected
    time.sleep(delay)
    
    with print_lock:
        print "No motion detection"
    motion_sensor._set_state(0) # stop motion
    motion_sensor.report_state()
    
    delay = 1 # delay after no motion before door closes
    time.sleep(delay)
    
    with print_lock:
        print "Door open"
    door_sensor._set_state(1) # indicates open
    door_sensor.report_state()
    
    close_door() # door takes delay normally distributed around 2 s to close
    
def simulate_person_entering():
    """
    Simulates the event that a person enters the house. In this case, the door 
    sensor will be triggered and some normally distributed time later, the motion 
    sensor is triggered.
    """
    with print_lock:
        print "Simulating person entering..."
        print "Door open"
    door_sensor._set_state(1) # indicates open
    door_sensor.report_state()
    
    threading.Thread(target=close_door, args=()).start()

    delay = 0.5 # time after door starts closing before motion starts
    
    with print_lock:
        print "Motion detected"
    motion_sensor._set_state(1) # motion detected
    motion_sensor.report_state()
    
    delay = 0.5 # time between motion and no motion
    time.sleep(delay)
    
    with print_lock:
        print "No motion detected"
    motion_sensor._set_state(0) # stop motion
    motion_sensor.report_state()
    
def simulate_beacon():
    """
    Simulates a beaconing indicating that the house owner has entered 
    and not an unauthorized person. There is a brief delay before the 
    beacon fires.
    """
    time.sleep(0.1)
    beacon.report_state()

simulate_person_leaving()
print "The security system's state is " + str(security_system.state) # should be 1 (on)
time.sleep(0.5)
threading.Thread(target=simulate_person_entering, args=()).start()
threading.Thread(target=simulate_beacon, args=()).start()
time.sleep(5) # must wait at least as long as the security system does for a beacon + delays in entering
print "The security system's state is " + str(security_system.state) # should be 0 (off)

time.sleep(3)
simulate_person_leaving()
print "The security system's state is " + str(security_system.state) # should be 1 (on)
time.sleep(0.5)
threading.Thread(target=simulate_person_entering, args=()).start()
time.sleep(5) # must wait at least as long as the security system does for a beacon + delays in entering
print "The security system's state is " + str(security_system.state) # should be -1 (intruder!)

print "Test complete."