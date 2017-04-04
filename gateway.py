# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 18:35:12 2017

@author: snoran

This class represents the IoT gateway.
"""

from sensor import Sensor
from server import MainServerSocket
import time
import json
import numpy as np
import Queue
import sys

debug = True

class Gateway(MainServerSocket):
    """
    The implementation of the IoT gateway, which acts as a server to which 
    multiple nodes (sensors and smart devices) can connect as clients.
    """
    def __init__(self, port):
        MainServerSocket.__init__(self, port)
        self.backend_id = 0 # assume backend is first to connect
        self.devices = {}
        self.leader_id = -1
        self.vector_clock = [0,0,0,0,0,0,0] # TODO
        self.queue = Queue.Queue()
        self.case = "door_opened" # or "motion_detected"; used to make a decision after querying the history
        self.mode = "HOME" # either "HOME" or "AWAY", assume "HOME" with initial setup
        self.beacon_fired = False
        
    def register(self, uuid, _type, name):
        """
        Registers an IoT node (a sensor or smart device) with 
        the gateway, specifying its type and name.
        
        type :  Either 'sensor' or 'smart device'
        name :  The name of the device, e.g. 'motion' for motion sensor
                or 'bulb' for smart light bulb.
        
        """
        self.devices[uuid]= ( _type, name)
        if debug:
            for uuid, device in self.devices.items():
                print uuid, device
            
    def send_to_backend(self, message):
        """
        Sends the message to the backend tier.
        """
        self.send_message(self.backend_id, message)
        
    def update_clock(self, sender, vector_clock):
#        print "before", self.vector_clock
#        print "other", vector_clock
#        print "after", self.vector_clock
        if sum(np.subtract(vector_clock, self.vector_clock)) > 1:
            self.queue.put((sender, vector_clock))
        else:
            self.vector_clock = list(np.maximum(self.vector_clock, vector_clock)) 
            while not self.queue.empty():
                item = self.queue.get()
                self.update_clock(item[0], item[1])
        
        
    def on_message_received(self, message):
        """
        Called when a message is received from one of the clients.
        """
#        print message
        message = json.loads(message)
#        print "received message with action : " + message['action']
        if message['action'] == 'register':
            if debug:
                print "Registering IoT unit..."
            self.register(message['uuid'], message['type'], message['name'])
        elif message['action'] == 'election':
            for i in range(int(message['uuid']) + 1, self.uuid):
                if debug:
                    print "sending to " + str(i)
                self.send_message(i, json.dumps({'action' : 'election', 'called_by' : message['uuid']}))
        elif message['action'] == 'election_response':
            self.send_message(int(message['respond_to']), json.dumps(message)) # forward to other clients
        elif message['action'] == 'election_won':
            if debug:
                print str(message['uuid']) + " won the election."
            self.leader_id = int(message['uuid'])
            for i in range(1, self.uuid):
                self.send_message(i, json.dumps(message)) # forward to all participants
        elif message['action'] == 'sync':
            for i in range(1, self.uuid):
                if i != message['uuid']: # ignore master
                    self.send_message(i, json.dumps(message)) # forward to slaves
        elif message['action'] == 'sync_response':
            self.send_message(message['respond_to'], json.dumps(message)) # forward response to master
        elif message['action'] == 'sync_complete':
            self.send_message(message['send_to'], json.dumps(message)) # forward to slaves
        elif message['action'] == 'report_state':
            message['vector_clock'] = list(np.maximum(self.vector_clock, message['vector_clock']))
            
            if self.devices[message['uuid']][1] == "door" and message['state'] == 1: # if the door is opened
                self.query_history(['door', 'motion'], [0, 1])
                self.case = "door_opened"
            elif self.devices[message['uuid']][1] == "motion" and message['state'] == 1:
                self.query_history(['door', 'motion'], [1, 0])
                self.case = "motion_detected"
            elif self.devices[message['uuid']][1] == "beacon":
                self.beacon_fired = True
            
            self.send_to_backend(json.dumps(message))
            self.update_clock(message['uuid'], message['vector_clock'])
            # update vector clock
            for i in range(1, self.uuid):
                if i != message['uuid']: # ignore self
                    self.send_message(i, json.dumps(message)) # send to all other clients
#            self.vector_clock = list(np.maximum(self.vector_clock, message['vector_clock']))
#            print "before", self.vector_clock
#            print "other", message['vector_clock']
#            print "after", self.vector_clock
                    
        elif message['action'] == 'report_history':
            most_recent_item = message['most_recent_item']
            print "Ok...", most_recent_item
            if len(most_recent_item.keys()) > 0:
                if self.case == "door_opened" and most_recent_item['name'] == 'motion':
                    if debug:
                        print "just left home"
                    self.mode = "AWAY"
                    self.turn_off_lights()
                    self.send_to_backend(json.dumps({'action' : 'user_left_home', 'timestamp' : most_recent_item['timestamp'], 'type' : 'gateway'}))
                    self.beacon_fired = False
                    for i in range(1, self.uuid):
                        if self.devices[i][1] == "security":
                            self.change_state(i, 1) # enable
                elif self.case == "motion_detected" and most_recent_item['name'] == 'door':
                    if debug:
                        print "just entered house"
                    self.mode = "HOME"
                    self.turn_on_lights()
                    self.send_to_backend(json.dumps({'action' : 'user_came_home', 'timestamp' : most_recent_item['timestamp'], 'type' : 'gateway'}))
                    time.sleep(3) # wait for beacon
                    for i in range(1, self.uuid):
                        if self.devices[i][1] == "security":
                            if self.beacon_fired:
                                self.change_state(i, 0) # disable
                                self.beacon_fired = False
                            else:
                                self.change_state(i, -1) # alarm
                                if debug:
                                    print "Burgalary!"
                            break
                    
                    
    def turn_on_lights(self):
        """
        Sends a message to turn ON the lights.
        """
        for i in range(1, self.uuid):
            if self.devices[i][1] == "bulb":
                self.change_state(i, 1)
                
    def turn_off_lights(self):
        """
        Sends a message to turn OFF the lights.
        """
        for i in range(1, self.uuid):
            if self.devices[i][1] == "bulb":
                self.change_state(i, 0)
                
    def change_state(self, device_id, state):
        message = {'action' : 'change_state', 'uuid' : device_id, 'type' : 'gateway', 'state' : state}
        self.send_to_backend(json.dumps(message))
        for i in range(1, self.uuid):
            self.send_message(i, json.dumps(message))
    
    def query_state(self, device_id):
        self.vector_clock[0] += 1
        message = {'action' : 'query_state', 'uuid' : device_id, 'type' : 'gateway'}
        self.send_to_backend(json.dumps(message))
        for i in range(1, self.uuid):
            self.send_message(i, json.dumps(message))
            
    def query_history(self, name_constraints, state_constraints):
        """
        Queries the database tier for all items with any of the given 
        name - state constraints, e.g. ["door", "motion"], [0, 1] will 
        query reports where the door is closed and where there is motion 
        detected, then return the most recent only, determined by timestamp 
        and by vector clock.
        """
        self.send_to_backend(json.dumps({'action' : 'query_history', 'name_constraints' : name_constraints, 'state_constraints' : state_constraints}))

if __name__=='__main__': 
    if len(sys.argv) > 1:
        if sys.argv[1] == '-f':
            debug = False
    gateway = Gateway(8881)
    gateway.launch()