# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 18:57:58 2017

@author: snoran

Base class for an IoT device, either a sensor or a smart device.
"""

from client import Client

class Device(Client):
    def __init__(self, address):
        """
        address : the address of the gateway to which the device should connect.
        """
        Client.__init__(self, address)
        self.uuid = -1
    
    def register(self):
        """
        Registers the device with the IoT gateway.
        """
        self.send_message({'uuid' : self.uuid, 'action' : 'register', 'type' : 'device', 'name' : 'bulb'})
        return
        
    def report_state(self):
        """
        Method stub for reporting the state of the device. This should be implemented by concrete subclasses.
        """
        # should be overridden in subclass
        return
        
    def change_state(self):
        """
        Method stub for changing the state of the device. This should be implemented by concrete subclasses.
        """
        # should be overridden in subclass
        return
        
    def on_message_received(self, message):
        """
        Called when a message is received by the device.
        """
        if message['action'] == 'query_state':
            self.report_state()
        elif message['action'] == 'register':
            self.uuid = message['uuid']
            print "my UUID is " + str(self.uuid)
            self.register()
        elif message['action'] == 'change_state':
            self.change_state()
            
            
        
if __name__=='__main__': 
    address = ('localhost', 8881)
    device = Device(address)
    device.connect()