# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 18:57:58 2017

@author: snoran

Base class for an IoT device, either a sensor or a smart device.
"""

from client import Client
import time
import numpy as np
import Queue
from threading import Lock
import sys

print_lock = Lock()

debug = True

class Device(Client):
    def __init__(self, address, _type, name):
        """
        address : the address of the gateway to which the device should connect.
        """
        Client.__init__(self, address)
        self._type = _type
        self.name = name
        self.state = 0
        self.uuid = -1
        self.election_lost = False
        self.leader_id = -1
        self.time_estimates = {}
        self.t0 = -1
        self.offset = 0
        self.vector_clock = [0,0,0,0,0,0,0] # TODO: Generalize to larger number of nodes
        self.queue = Queue.Queue()
    
    def register(self):
        """
        Registers the device with the IoT gateway.
        """
        self.send_message({'uuid' : self.uuid, 'action' : 'register', 'type' : self._type, 'name' : self.name})
        return
        
    def report_state(self):
        """
        Reports the sensor state to the gateway.
        """
        if debug:
            with print_lock :
                print "node " + str(self.uuid) + " : " + self.name
                print "my clock:", self.vector_clock
                print "\n"
        self.vector_clock[self.uuid] += 1
        self.send_message({'uuid' : self.uuid, 'action' : 'report_state', 'state' : self.state, 'timestamp' : time.time() - self.offset, 'vector_clock' : self.vector_clock, 'name' : self.name})
        
    def change_state(self, state):
        """
        Sets the state of the device. TODO: If _type is 'sensor', throw exception
        """
        self.state = state
        self.report_state()
        return
        
    def _set_state(self, state):
        self.state = state
        
    def start_election(self):
        self.send_message({'uuid' : self.uuid, 'action' : 'election'})
        self.election_lost = False
        time.sleep(0.5)
        if not self.election_lost:
            self.send_message({'uuid' : self.uuid, 'action' : 'election_won'})
            self.election_won()
            
    def election_won(self):
        self.time_estimates = {}
        self.send_message({'uuid' : self.uuid, 'action' : 'sync'}) # master in Berkeley sync algorithm
        self.t0 = time.time()
        time.sleep(0.5) # wait for all responses (those that take too long can be ignored)
        tf = time.time()
        keys = self.time_estimates.keys()
        if debug:
            print "received sync responses from " + str(len(keys)) + " nodes."
        avg_time = 0
        for k in keys:
            avg_time += self.time_estimates[k]
        avg_time += self.t0 + (tf - self.t0) / 2 # include self
        avg_time = avg_time / (len(keys) + 1)
        for k in keys:
            self.send_message({'uuid' : self.uuid, 'send_to' : k, 'action' : 'sync_complete', 'offset' : (self.time_estimates[k] - avg_time)})    
    
    def update_clock(self, sender, vector_clock):
        with print_lock:
#            print "node " + str(self.uuid)
#            print "before", self.vector_clock
#            print "other", vector_clock
            if sum(np.subtract(vector_clock, self.vector_clock)) > 1:
                self.queue.put((sender, vector_clock))
            else:
                self.vector_clock = list(np.maximum(self.vector_clock, vector_clock)) 
                while not self.queue.empty():
                    item = self.queue.get()
                    self.update_clock(item[0], item[1])
#            print "after", self.vector_clock
#            print "\n"
    
    def on_message_received(self, message):
        """
        Called when a message is received by the device.
        """
        if message['action'] == 'query_state':
            self.update_clock(message['uuid'], message['vector_clock'])
            if message['uuid'] == self.uuid:
                self.report_state()
        elif message['action'] == 'register':
            self.uuid = message['uuid']
            if debug:
                print "UUID of " + self.name + " is " + str(self.uuid) # + ". Calling election."
            self.register()
#            self.start_election()
        elif message['action'] == 'change_state':
            self.change_state(message['state'])
        elif message['action'] == 'election':
            if debug:
                print self.name + " received notification that an election was called by " + str(message['called_by']) + ". Calling new election."
            self.send_message({'uuid' : self.uuid, 'action' : 'election_response', 'respond_to' : message['called_by']})
            self.start_election()
        elif message['action'] == 'election_response':
            if debug:
                print self.name + " has lost the election."
            self.election_lost = True
        elif message['action'] == 'election_won':
            if debug:
                print self.name + " received notification that the election was won by " + str(message['uuid'])
            self.leader_id = int(message['uuid'])
        elif message['action'] == 'sync':
            self.send_message({'uuid' : self.uuid, 'action' : 'sync_response', 'timestamp' : time.time(), 'respond_to' : message['uuid']})
        elif message['action'] == 'sync_response':
            t_reply = (time.time() - self.t0) / 2
            if debug:
                print "Received a reply from " + str(message['uuid']) + " with TOF " + str(t_reply)
            self.time_estimates[message['uuid']] = message['timestamp'] + t_reply
        elif message['action'] == 'sync_complete':
            self.offset = message['offset']
            if debug:
                print self.name + " has an offset of " + str(self.offset)
        elif message['action'] == 'report_state':
            self.update_clock(message['uuid'], message['vector_clock'])
            
            
        
if __name__=='__main__': 
    if len(sys.argv) > 1:
        if sys.argv[1] == '-f':
            debug = False
            
    address = ('localhost', 8881)
    temperature_sensor = Device(address, 'sensor', 'temperature')
    temperature_sensor.connect()
    
    time.sleep(0.5)
    
    motion_sensor = Device(address, 'sensor', 'motion')
    motion_sensor.connect()
    
    time.sleep(0.5)
    
#    motion_sensor.disconnect()
#    
#    time.sleep(0.5)
    
    temperature_sensor.start_election()
    
    time.sleep(2)
    
    temperature_sensor.report_state()
    motion_sensor.report_state()
#    motion_sensor.report_state()
#    motion_sensor.report_state()
#    temperature_sensor.report_state()
#    motion_sensor.report_state()
#    temperature_sensor.report_state()
#    motion_sensor.report_state()
#    motion_sensor.report_state()
#    motion_sensor.report_state()
#    temperature_sensor.report_state()
#    motion_sensor.report_state()