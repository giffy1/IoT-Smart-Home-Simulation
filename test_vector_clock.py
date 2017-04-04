# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 20:40:01 2017

@author: snoran

This script tests the vector clock implementation. Sensors periodically send 
out state reports to the gateway and this script checks to make sure that 
the vector clocks of each device is correct.

For this test, we do not initiate the leader election algorithm or perform 
Berkeley synchronization, because we know all devices are already snychronized 
because they are using the same machine's clock. On a real distributed 
system with no global clock and clock drift, we would have to use the 
synchronization, but for testing purposes we omit it.

"""

import device
from device import Device
import time
import numpy as np
from threading import Lock
import sys

if len(sys.argv) > 1:
    if sys.argv[1] == '-f':
        device.debug = False

print_lock = Lock()

devices = []

final_clock = [0,0,0,0,0,0,0]

# first set up the IoT system:
address = ('localhost', 8881)
temperature_sensor = Device(address, 'sensor', 'temperature')
temperature_sensor.connect()
devices.append(temperature_sensor)

time.sleep(0.5)

motion_sensor = Device(address, 'sensor', 'motion')
motion_sensor.connect()
devices.append(motion_sensor)

time.sleep(0.5)

door_sensor = Device(address, 'sensor', 'door')
door_sensor.connect()
devices.append(door_sensor)

n_trials = 10
for i in range(n_trials):
    # select device randomly for reporting
    device_index = np.random.randint(0,3)
    d = devices[device_index]
    d.report_state()
    final_clock[device_index+1] += 1
    with print_lock:
        print "Device " + str(d.uuid) + " (" + d.name + ") reporting its state."

time.sleep(0.5) # wait for outgoing messages before comparing final clocks
for d in devices:
    assert d.vector_clock == final_clock
    print "Device " + str(d.uuid) + " (" + d.name + ") has vector clock " + str(d.vector_clock)

print "Correct clock :"
print final_clock
    
print "Test complete."