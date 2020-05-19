# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

"""
Server
++++++

The :file:`server.py` example file is a demonstrator echo server.
It uses a subclass of :class:`SlipRequestHandler`
that transforms the :attr:`request` attribute into
a dedicated socket subclass that prints
the raw data that is received and sent.
The request handler prints the decoded message,
and then reverses the order of the bytes in the encoded message
(so ``abc`` becomes ``cab``),
and sends it back to the client.
"""

import socket
import sys
from socketserver import TCPServer

from _socket import dup  # type: ignore
from sliplib import SlipRequestHandler


class _ChattySocket(socket.socket):
    """A socket subclass that prints the raw data that is received and sent."""

    def __init__(self, sock):
        fd = dup(sock.fileno())
        super().__init__(sock.family, sock.type, sock.proto, fileno=fd)
        super().settimeout(sock.gettimeout())

    def recv(self, chunksize):
        data = super().recv(chunksize)
        print('Raw data received:', data)
        return data

    def sendall(self, data):
        print('Sending raw data:', data)
        super().sendall(data)


class SlipHandler(SlipRequestHandler):
    """A SlipRequestHandler that echoes the received message with the bytes in reversed order."""

    def setup(self):
        self.request = _ChattySocket(self.request)
        print("Incoming connection from {}".format(self.request.getpeername()))
        super().setup()

    # Dedicated handler to show the encoded bytes.
    def handle(self):
        while True:
            message = self.request.recv_msg()
            print('Decoded data:', message)
            if message:
                self.request.send_msg(bytes(reversed(message)))
            else:
                print('Closing down')
                break


class TCPServerIPv6(TCPServer):
    """An IPv6 TCPServer"""
    address_family = socket.AF_INET6


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'ipv6':
        server = TCPServerIPv6(('localhost', 0), SlipHandler)  # type: TCPServer
    else:
        server = TCPServer(('localhost', 0), SlipHandler)
    print('Slip server listening on localhost, port', server.server_address[1])
    server.handle_request()
