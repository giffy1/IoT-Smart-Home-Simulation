# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 18:57:58 2017

@author: snoran

Base class for an IoT device, either a sensor or a smart device.
"""

from client import Client
import time

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
        self.send_message({'uuid' : self.uuid, 'action' : 'report_state', 'state' : self.state, 'timestamp' : time.time() - self.offset})
        
    def change_state(self, state):
        """
        Sets the state of the device. TODO: If _type is 'sensor', throw exception
        """
        self.state = state
        self.report_state()
        return
        
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
        print "received sync responses from " + str(len(keys)) + " nodes."
        avg_time = 0
        for k in keys:
            avg_time += self.time_estimates[k]
        avg_time += self.t0 + (tf - self.t0) / 2 # include self
        avg_time = avg_time / (len(keys) + 1)
        for k in keys:
            self.send_message({'uuid' : self.uuid, 'send_to' : k, 'action' : 'sync_complete', 'offset' : (self.time_estimates[k] - avg_time)})
        
    def on_message_received(self, message):
        """
        Called when a message is received by the device.
        """
        if message['action'] == 'query_state':
            self.report_state()
        elif message['action'] == 'register':
            self.uuid = message['uuid']
            print "UUID of " + self.name + " is " + str(self.uuid) + ". Calling election."
            self.register()
#            self.start_election()
        elif message['action'] == 'change_state':
            self.change_state(message['state'])
        elif message['action'] == 'election':
            print self.name + " received notification that an election was called by " + str(message['called_by']) + ". Calling new election."
            self.send_message({'uuid' : self.uuid, 'action' : 'election_response', 'respond_to' : message['called_by']})
            self.start_election()
        elif message['action'] == 'election_response':
            print self.name + " has lost the election."
            self.election_lost = True
        elif message['action'] == 'election_won':
            print self.name + " received notification that the election was won by " + str(message['uuid'])
            self.leader_id = int(message['uuid'])
        elif message['action'] == 'sync':
            self.send_message({'uuid' : self.uuid, 'action' : 'sync_response', 'timestamp' : time.time(), 'respond_to' : message['uuid']})
        elif message['action'] == 'sync_response':
            t_reply = (time.time() - self.t0) / 2
            print "Received a reply from " + str(message['uuid']) + " with TOF " + str(t_reply)
            self.time_estimates[message['uuid']] = message['timestamp'] + t_reply
        elif message['action'] == 'sync_complete':
            self.offset = message['offset']
            print self.name + " has an offset of " + str(self.offset)
            
            
        
if __name__=='__main__': 
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