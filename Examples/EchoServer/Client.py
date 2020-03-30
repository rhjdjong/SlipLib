# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

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
        sock.sendall(driver.send(message))
        rcvd = sock.recv(1024)
        messages = driver.receive(rcvd)
        print(messages)
