# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

# pylint: disable=attribute-defined-outside-init

"""Tests for SlipRequestHandler"""

from socket import AF_INET, AF_INET6  # pylint: disable=no-name-in-module
from socket import socket
import socketserver
import threading

import pytest

from sliplib import SlipRequestHandler, SlipSocket, END


class DummySlipRequestHandler(SlipRequestHandler):
    """SlipRequestHandler subclass that handles a single packet."""
    def handle(self):
        assert isinstance(self.request, SlipSocket)
        msg = self.request.recv_msg()
        assert msg == b'hallo'
        self.request.send_msg(bytes(reversed(msg)))


class TestSlipRequestHandler:
    """Tests for SlipRequestHandler."""

    @pytest.fixture(autouse=True, params=[
        (AF_INET, ('127.0.0.1', 0)),
        (AF_INET6, ('::1', 0, 0, 0))
    ])
    def setup(self, request):
        """Prepare the test."""
        self.family = request.param[0]
        self.bind_address = request.param[1]
        # Cannot use standard TCPServer, because that is hardcoded to IPv4
        self.server_class = type('SlipServer',
                                 (socketserver.TCPServer,),
                                 {"address_family": self.family})
        self.client_socket = socket(family=self.family)
        self.server_is_running = threading.Event()
        yield
        self.client_socket.close()

    def server(self, bind_address):
        """Create a server."""
        srv = self.server_class(bind_address, DummySlipRequestHandler)
        self.server_address = srv.server_address
        self.server_is_running.set()
        srv.handle_request()

    def test_working_of_sliprequesthandler(self):
        """Verify that the server returns the message with the bytes in reversed order."""
        server_thread = threading.Thread(target=self.server, args=(self.bind_address,))
        server_thread.start()
        self.server_is_running.wait(0.5)
        self.client_socket.connect(self.server_address)
        self.client_socket.sendall(END + b'hallo' + END)
        response = self.client_socket.recv(4096)
        assert response == END + b'ollah' + END
        server_thread.join()
