# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 12:10:03 2017

@author: snoran

Back-end tier of the gateway, which is responsible for interfacing with the 
database. It can function as the client in the client-server communication
with the gateway.

"""

from client import Client

class Backend(Client):
    def __init__(self, address):
        """
        address : the address of the gateway to which the device should connect.
        """
        Client.__init__(self, address)
        
    def on_message_received(self, message):
        """
        Called when a message is received by the device.
        """
        if message['action'] == 'query_history':
            print "TODO"
#        else:
#            with open("database.txt", "a") as f:
#                f.write(message)
                
if __name__=='__main__': 
    address = ('localhost', 8881)
    backend = Backend(address)
    backend.connect()