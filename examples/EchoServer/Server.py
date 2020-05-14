# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

"""
Server
++++++

The :file:`Server.py` example file is a demonstrator echo server.
It uses a subclass of :class:`SlipRequestHandler`
that transforms the :attr:`request` attribute into
a dedicated socket subclass that prints
the raw data that is received and sent.
The request handler prints the decoded message,
and then reverses the order of the bytes in the encoded message
(so ``abc`` becomes ``cab``),
and sends it back to the client.
"""

from sliplib import SlipRequestHandler
from socketserver import TCPServer
import socket
from _socket import dup


class ChattySocket(socket.socket):
    def __init__(self, sock):
        fd = dup(sock.fileno())
        super().__init__(sock.family, sock.type, sock.proto, fileno=fd)
        super().settimeout(sock.gettimeout())

    def recv(self, chunksize):
        data = super().recv(chunksize)
        print('raw data received:', data)
        return data

    def sendall(self, data):
        print('sending raw data:', data)
        super().sendall(data)


class SlipHandler(SlipRequestHandler):
    def setup(self):
        self.request = ChattySocket(self.request)
        super().setup()

    # Dedicated handler to show the encoded bytes.
    def handle(self):
        while True:
            message = self.request.recv_msg()
            print('decoded data:', message)
            if message:
                self.request.send_msg(bytes(reversed(message)))
            else:
                print('closing down')
                break


if __name__ == '__main__':
    server = TCPServer(('localhost', 0), SlipHandler)
    print('Slip server listening on', server.server_address)
    server.handle_request()
