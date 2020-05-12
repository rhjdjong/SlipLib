#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.


import pytest
from multiprocessing import Pipe, Process
from sliplib import SlipRequestHandler, SlipSocket
from socketserver import TCPServer


class SlipEchoHandler(SlipRequestHandler):
    def handle(self):
        while True:
            message = self.request.recv_msg()
            if not message:
                break
            # Reverse the order of the bytes and send it back.
            data_to_send = bytes(reversed(message))
            self.request.send_msg(data_to_send)


class SlipEchoServer:
    def __init__(self, pipe):
        self.server = TCPServer(('localhost', 0), SlipEchoHandler)
        pipe.send(self.server.server_address)
        self.server.handle_request()


class SlipEchoClient:
    def __init__(self, address):
        self.sock = SlipSocket.create_connection(address)

    def echo(self, msg):
        self.sock.send_msg(msg)
        return self.sock.recv_msg()


class TestEchoServer:
    @pytest.fixture(autouse=True)
    def setup(self):
        near, far = Pipe()
        self.server = Process(target=SlipEchoServer, args=(far,))
        self.server.start()
        server_address = near.recv()
        self.client = SlipEchoClient(server_address)
        yield
        self.client.sock.close()
        self.server.join()

    def test_echo_server(self):
        data = [
            (b'hallo', b'ollah'),
            (b'goodbye', b'eybdoog')
        ]
        for snd_msg, expected_reply in data:
            assert self.client.echo(snd_msg) == expected_reply
