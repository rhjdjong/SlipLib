#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

# pylint: disable=attribute-defined-outside-init

"""
This module tests SlipSocket using a SLIP echo server, similar to the one in the examples directory.
"""

from multiprocessing import Pipe, Process
from socketserver import TCPServer
import pytest
from sliplib import SlipRequestHandler, SlipSocket


class SlipEchoHandler(SlipRequestHandler):
    """SLIP request handler that echoes the received message, but with the bytes in reversed order."""
    def handle(self):
        while True:
            message = self.request.recv_msg()
            if not message:
                break
            # Reverse the order of the bytes and send it back.
            data_to_send = bytes(reversed(message))
            self.request.send_msg(data_to_send)


class SlipEchoServer:  # pylint: disable=too-few-public-methods
    """Execution helper for the echo server. Sends the server address back over the pipe."""
    def __init__(self, pipe):
        self.server = TCPServer(('localhost', 0), SlipEchoHandler)
        pipe.send(self.server.server_address)
        self.server.handle_request()


class SlipEchoClient:
    """Client for the SLIP echo server"""
    def __init__(self, address):
        self.sock = SlipSocket.create_connection(address)

    def echo(self, msg):
        """Send message to the SLIP server and returns the response."""
        self.sock.send_msg(msg)
        return self.sock.recv_msg()

    def close(self):
        """Close the SLIP socket"""
        self.sock.close()


class TestEchoServer:
    """Test for the SLIP echo server"""
    @pytest.fixture(autouse=True)
    def setup(self):
        """Prepare the server and client"""
        near, far = Pipe()
        self.server = Process(target=SlipEchoServer, args=(far,))
        self.server.start()
        server_address = near.recv()
        self.client = SlipEchoClient(server_address)
        yield
        self.client.close()
        self.server.join()

    def test_echo_server(self):
        """Test the echo server"""
        data = [
            (b'hallo', b'ollah'),
            (b'goodbye', b'eybdoog')
        ]
        for snd_msg, expected_reply in data:
            assert self.client.echo(snd_msg) == expected_reply
