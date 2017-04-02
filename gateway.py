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
        self.devices = {}
        
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
        
    def on_message_received(self, message):
        """
        Called when a message is received from one of the clients.
        """
        print message
        message = json.loads(message)
        print "received message with action : " + message['action']
        if message['action'] == 'register':
            print "Registering IoT unit..."
            self.register(message['uuid'], message['type'], message['name'])
        return
        
    def query_state(self, device_id):
        self.send_message(device_id, json.dumps({'action' : 'query_state'}))
        

if __name__=='__main__': 
    gateway = Gateway(8881)
    gateway.launch()