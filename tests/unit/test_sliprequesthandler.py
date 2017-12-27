# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import pytest

import socket
import socketserver
import threading

from sliplib import SlipRequestHandler, SlipSocket, END


class DummySlipRequestHandler(SlipRequestHandler):
    def handle(self):
        assert isinstance(self.request, SlipSocket)
        msg = self.request.recv_msg()
        assert msg == b'hallo'
        self.request.send_msg(bytes(reversed(msg)))
        self.request.close()


# noinspection PyAttributeOutsideInit
class TestSlipRequestHandler:
    @pytest.fixture(autouse=True, params=[
        socket.AF_INET,
        socket.AF_INET6
    ])
    def setup(self, request):
        self.family = request.param
        self.ServerClass = type('SlipServer',
                                (socketserver.TCPServer,),
                                {"address_family": self.family})
        self.client_socket = socket.socket(family=self.family)
        self.server_is_running = threading.Event()
        yield
        self.client_socket.close()

    def server(self, ip_address):
        srv = self.ServerClass((ip_address, 0), DummySlipRequestHandler)
        self.server_address = srv.server_address
        self.server_is_running.set()
        srv.handle_request()

    # noinspection PyPep8Naming
    def test_sliprequesthandler_contains_SlipSocket(self):
        server_thread = threading.Thread(target=self.server, args=('localhost',))
        server_thread.start()
        self.server_is_running.wait(0.5)
        self.client_socket.connect(self.server_address)
        self.client_socket.sendall(END + b'hallo' + END)
        response = self.client_socket.recv(4096)
        assert response == END + b'ollah' + END
        server_thread.join()
