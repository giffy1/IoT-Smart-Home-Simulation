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
        
    def register(self, uuid, _type, name):
        """
        Registers an IoT node (a sensor or smart device) with 
        the gateway, specifying its type and name.
        
        type :  Either 'sensor' or 'smart device'
        name :  The name of the device, e.g. 'motion' for motion sensor
                or 'bulb' for smart light bulb.
        
        """
        self.devices[uuid]= ( _type, name)
        for uuid, device in self.devices.items():
            print uuid, device
            
    def send_to_backend(self, message):
        """
        Sends the message to the backend tier.
        """
        self.send_message(self.backend_id, message)
        
        
    def on_message_received(self, message):
        """
        Called when a message is received from one of the clients.
        """
        print message
#        self.send_to_backend(message)
        message = json.loads(message)
        print "received message with action : " + message['action']
        if message['action'] == 'register':
            print "Registering IoT unit..."
            self.register(message['uuid'], message['type'], message['name'])
        elif message['action'] == 'election':
            for i in range(int(message['uuid']) + 1, self.uuid):
                print "sending to " + str(i)
                self.send_message(i, json.dumps({'action' : 'election', 'called_by' : message['uuid']}))
        elif message['action'] == 'election_response':
            self.send_message(int(message['respond_to']), json.dumps(message)) # forward to other clients
        elif message['action'] == 'election_won':
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
        
    def query_state(self, device_id):
        self.send_message(device_id, json.dumps({'action' : 'query_state'}))
        

if __name__=='__main__': 
    gateway = Gateway(8881)
    gateway.launch()