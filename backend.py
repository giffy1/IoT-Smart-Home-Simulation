# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 12:10:03 2017

@author: snoran

Back-end tier of the gateway, which is responsible for interfacing with the 
database. It can function as the client in the client-server communication
with the gateway.

"""

from client import Client
import json
import sys

debug= True

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
            latest_timestamp = 0
            latest_item = {}
            with open("database.txt", "rb") as f:
                for i, line in enumerate(f):
                    item = json.loads(line)
                    for name,state in zip(message['name_constraints'], message['state_constraints']):
                        if item['name'] == name and item['state'] == state:
                            timestamp = item['timestamp']
                            if timestamp > latest_timestamp:
                                latest_item = item
                                latest_timestamp = item['timestamp']
                            break
                        
            # report the most recent match to the given DB query (could return all, but for simplicity, the front-end tier really only needs the most recent)
            self.send_message({'action' : 'report_history', 'most_recent_item' : latest_item})
                    
        elif message['action'] == 'query_state' or message['action'] == 'report_state':
            with open("database.txt", "a") as f:
                f.write(json.dumps(message) + '\n')
                
if __name__=='__main__': 
    if len(sys.argv) > 1:
        if sys.argv[1] == '-f':
            debug = False
    address = ('localhost', 8881)
    backend = Backend(address)
    backend.connect()