# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 19:15:40 2017

@author: snoran
"""

import json
import Queue
import threading
import socket

exit_flag = 0

def receive_message(socket, callback = None):
    """
    Receives messages through the given socket and upon receiving messages, 
    passes them to the given callback, if provided.
    """
    while not exit_flag:
        try:
            message = socket.recv(1024)
            if message:
                if callback:
                    callback(json.loads(message))
        except Exception as err:
            if err.message == "timed out":
                pass
            else:
                print err
    
def send_message(socket, queue_lock, message_queue):
    """
    Safely sends messages from the given queue through the given socket.
    """
    while not exit_flag:                    
        queue_lock.acquire()
        if not message_queue.empty():
            message = message_queue.get()
            socket.send(json.dumps(message))
        queue_lock.release()

class Client():
    def __init__(self, address):
        self.address = address
        self.message_queue = Queue.Queue()
        self.queue_lock = threading.Lock()
    
    def connect(self):
        """
        Establishes a socket connection to the server and starts consumer and 
        producer threads for communicating with the server.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.address)
        print "Connected to server"
        
        threading.Thread(target=receive_message, args=(self.socket, self.on_message_received)).start()
        threading.Thread(target=send_message, args=(self.socket, self.queue_lock, self.message_queue)).start() 
        
    def disconnect(self):
        self.socket.close()
        global exit_flag
        exit_flag = 1
        
    def send_message(self, message):
        """
        Adds a message to the queue to be sent to the server.
        
        Messages are by convention in JSON format.
        """
        
        self.queue_lock.acquire()
#        time.sleep(self.delay)
        self.message_queue.put(message)
        self.queue_lock.release()
        
    def on_message_received(self, message):
        # do nothing, allow subclasses to override this
        return