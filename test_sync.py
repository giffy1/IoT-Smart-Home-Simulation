# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 20:40:01 2017

@author: snoran

Test the leader election and Berkeley clock synchronization algorithms. 
To do this, we'll deploy the full IoT network. Then over a number of trials,
a random client calls for an election. After each trial, the process with 
the highest ID should be the leader. This should always be the smart light 
bulb. Also, every node should know that the smart light bulb is the leader, 
which can be checked using its leader_id field.

Since all devices are running locally on the same machine and have the same 
physical clock, they are actually never out of sync. This allows us to test 
the clock synchronization algorithm very effectively: We expect the offsets 
to be very close to 0. Any difference is due to error in the estimation of 
t_reply. We could plot the distribution of offsets to check this, but I 
simply check it against a reasonable threshold. How I choose the threshold 
is described at the bottom in the in-line comment.

To run the test, first run gateway.py to start the server. Then run backend.py 
to start up the backend tier. Lastly, run this script.

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
    with print_lock:
        print "Leader election trial " + str(i)
    device_index = np.random.randint(0,3)
    devices[device_index].start_election()
    time.sleep(1)

    for d in devices:
        assert d.leader_id == 3
        with print_lock:
            print "Device " + str(d.uuid) + " (" + d.name + ") recognizes " + str(d.leader_id) + " as the leader."
    
    for d in devices:
        # the Berkeley algorithm claims to achieve synchronization within 0.04 seconds (40 ms). However, 
        # because in my network, the clients do not communicate with one another at all, but must 
        # communicate through the gateway, there is an additional delay in client-client communication. 
        # Therefore I double the bound and add a bit of an extra buffer. It should definitely be within 100 ms with very high certainty.
        assert np.abs(d.offset) < 0.1 
        with print_lock:
            print "Device " + str(d.uuid) + " (" + d.name + ") has an offset of " + str(d.offset)

    
print "Test complete."