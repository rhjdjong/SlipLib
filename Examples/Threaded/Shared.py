'''
Created on 24 aug. 2016

@author: Ruud
'''

import threading
import queue
import socket

import sliplib

class SlipConnection:
    def __init__(self, sock):
        self.sock = sock
        timeout = self.sock.gettimeout()
        if not timeout:
            self.sock.settimeout(0.1)
            
        self.driver = sliplib.Driver()
        self.message_q = queue.Queue()
        self.packet_q = queue.Queue()
        self.running = True
        self.connection_closed = threading.Event()
        
        self.recv_thread = threading.Thread(target=self.receive_data)
        self.send_thread = threading.Thread(target=self.send_data)
        self.recv_thread.start()
        self.send_thread.start()
        
        self.connection_closed.wait()
        self.running = False
        self.recv_thread.join(0.5)
        self.send_thread.join(0.5)
        
    
    def send(self, message):
        self.packet_q.put(self.driver.send(message))
    
    def recv(self, timeout=None):
        return self.message_q.get(timeout=timeout)
    
    def receive_data(self):
        while self.running:
            try:
                data = self.sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                # Socket error. Signal this to the other threads, and terminate
                self.connection_closed.set()
                break
            
            if not data:
                # Connection is closed. Signal this to the other threads, and terminate
                self.connection_closed.set()
                break
            else:
                self.driver.receive(data)
                for m in self.driver.messages:
                    self.message_q.put(m)
    
    def send_data(self):
        while self.running:
            try:
                packet_lst = [self.packet_q.get(timeout=0.1)]
            except queue.Empty:
                continue

            try:
                while True:
                    packet_lst.append(self.packet_q.get(block=False))
            except queue.Empty:
                pass
            try:
                self.sock.sendall(b''.join(packet_lst))
            except OSError:
                # Socket error. Signal this to the other threads, and terminate
                self.connection_closed.set()
                break
            

