# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 19:16:07 2017

@author: snoran

"""

import asyncore, asynchat, socket, json

class MainServerSocket(asyncore.dispatcher):
    def __init__(self, port):
        print 'initializing main server socket'
        asyncore.dispatcher.__init__(self)
        self.clients = []
        self.uuid = 0
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('',port))
        self.listen(5)
        
    def launch(self):
        """
        Starts running the server.
        """
        asyncore.loop()
    
    def on_message_received(self, message):
        """
        Called when the server receives a message.
        """
        # do nothing, allow subclasses to override this
        return
        
    def handle_accept(self):
        """
        Called when a client connects to the server. Immediately assign the 
        client a unique ID and notify the client.
        """
        newSocket, address = self.accept()
        print "Connected from", address
        self.clients.append(SecondaryServerSocket(self.on_message_received, newSocket))
        self.clients[-1].push(json.dumps({'action' : 'register', 'uuid' : self.uuid}))
        self.uuid += 1
        
    def send_message(self, uuid, message):
        """
        Sends a message to a particular client.
        
        uuid : the unique ID identifying the client.
        message : the message being sent to the client.
        """
        print message, uuid
        print "sending..."
        self.clients[uuid].push(message)

class SecondaryServerSocket(asynchat.async_chat):
    def __init__(self, callback, *args):
        self.callback = callback
        print 'initializing secondary server socket'
        asynchat.async_chat.__init__(self, *args)
        
    def collect_incoming_data(self, data):
        self.callback(data)
        
    def handle_close(self):
        print "Disconnected from", self.getpeername()
        self.close()

if __name__=='__main__': 
    MainServerSocket(8881)
    #asyncore.loop()