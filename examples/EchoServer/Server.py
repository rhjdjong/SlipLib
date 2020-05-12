# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

"""
Server
++++++

The :file:`Server.py` example file is a demonstrator echo server.
It prints both the
received raw data it receives from a client and the decoded messages.
It then reverses the order of the bytes in the encoded message
(so ``abc`` becomes ``cab``),
prints out the encoded byte string, and sends it back to the client.
"""

from sliplib import Driver
from socketserver import TCPServer, BaseRequestHandler


class SlipHandler(BaseRequestHandler):
    def setup(self):
        self.driver = Driver()

    # Dedicated handler to show the encoded bytes.
    def handle(self):
        stop = False
        while not stop:
            data = self.request.recv(1024)
            if data:
                print('raw data received:', data)
            else:
                print('closing down')
                stop = True

            messages = self.driver.receive(data)
            if messages:
                print('decoded data:')
                for msg in messages:
                    print(msg)
                    data_to_send = self.driver.send(bytes(reversed(msg)))
                    print('raw data to send:', data_to_send)
                    self.request.sendall(data_to_send)


if __name__ == '__main__':
    server = TCPServer(('localhost', 0), SlipHandler)
    print('Slip server listening on', server.server_address)
    server.handle_request()
