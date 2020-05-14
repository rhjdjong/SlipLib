# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

"""
Client
++++++

The :file:`Client.py` example file is a client for the demonstrator echo server .
It prompts the user for a message,
encodes it in a Slip packet, sends it to the server,
and prints the decoded reply it gets back from the server.
This is repeated until the user enters an empty message.
"""

import sys

import sliplib

if __name__ == '__main__':
    host, port = sys.argv[1:3]
    print("Connecting to {}, port {}".format(host, port))
    sock = sliplib.SlipSocket.create_connection((host, int(port)))

    while True:
        message = input('Message>')
        if not message:
            break
        message = bytes(message, 'utf-8')
        sock.send_msg(message)
        message = sock.recv_msg()
        print(message)
