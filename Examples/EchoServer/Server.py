"""
Created on 24 aug. 2016

@author: Ruud
"""

from sliplib import encode, decode
from socketserver import TCPServer, BaseRequestHandler


class SlipHandler(BaseRequestHandler):
    # Dedicated handler to show the encoded bytes.
    def handle(self):
        while True:
            data = self.request.recv(1024)
            if not data:
                break
            
            print('raw data received:', data)
            message = decode(data)
            print('decoded data:', message)

            data_to_send = encode(bytes(reversed(message)))
            print('raw data to send:', data_to_send)
            self.request.sendall(data_to_send)


if __name__ == '__main__':
    server = TCPServer(('localhost', 0), SlipHandler)
    print('Slip server listening on', server.server_address)
    server.handle_request()
