# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 16:18:49 2017

@author: snoran
"""

from device import Device
import time
import numpy as np
import threading
from threading import Lock

print_lock = Lock()

# first set up the IoT system:
address = ('localhost', 8881)
temperature_sensor = Device(address, 'sensor', 'temperature')
temperature_sensor.connect()

time.sleep(0.5)

motion_sensor = Device(address, 'sensor', 'motion')
motion_sensor.connect()

time.sleep(0.5)

door_sensor = Device(address, 'sensor', 'door')
door_sensor.connect()

temperature_sensor.start_election()

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
        delay = np.random.normal(7, 4)
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
    
    delay = np.random.rand()*5
    time.sleep(delay)
    
    with print_lock:
        print "No motion detection"
    motion_sensor._set_state(0) # stop motion
    motion_sensor.report_state()
        
    delay = 0
    while delay < 0.5:
        delay = np.random.normal(5, 3)
    time.sleep(delay)
    
    with print_lock:
        print "Door open"
    door_sensor._set_state(1) # indicates open
    door_sensor.report_state()
    
    close_door()
    
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

    delay = 0
    while delay < 0.5:
        delay = np.random.normal(5, 3)
    time.sleep(delay)
    
    with print_lock:
        print "Motion detected"
    motion_sensor._set_state(1) # motion detected
    motion_sensor.report_state()
    
    delay = np.random.rand()*10 
    time.sleep(delay)
    
    with print_lock:
        print "No motion detected"
    motion_sensor._set_state(0) # stop motion
    motion_sensor.report_state()

simulate_person_leaving()
time.sleep(2)
simulate_person_entering()

#temperature_sensor.report_state()
#motion_sensor.report_state()