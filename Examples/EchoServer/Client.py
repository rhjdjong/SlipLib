'''
Created on 24 aug. 2016

@author: Ruud
'''

import socket
import sys

import sliplib

if __name__ == '__main__':
    host, port = sys.argv[1:3]
    sock = socket.create_connection((host, port))
    driver = sliplib.Driver()
    
    while True:
        message = input('Message>')
        if not message:
            break
        message = bytes(message, 'utf-8')
        driver.send(message)
        data = driver.packets
        sock.sendall(data)
        rcvd = sock.recv(1024)
        driver.receive(rcvd)
        messages = driver.messages
        print(messages)
            
