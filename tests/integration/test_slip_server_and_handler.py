# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.


"""Tests for SlipRequestHandler"""

from __future__ import annotations

import threading
from socket import AF_INET, AF_INET6, socket
from typing import TYPE_CHECKING, Generator

import pytest

from sliplib import END, SlipRequestHandler, SlipServer, SlipSocket

if TYPE_CHECKING:
    from sliplib.slipsocket import TCPAddress


class DummySlipRequestHandler(SlipRequestHandler):
    """SlipRequestHandler subclass that handles a single packet."""

    def handle(self) -> None:
        assert isinstance(self.request, SlipSocket)
        msg = self.request.recv_msg()
        assert msg == b"hallo"
        self.request.send_msg(bytes(reversed(msg)))


@pytest.mark.parametrize(
    ("family", "address"),
    (
        (AF_INET, ("127.0.0.1", 0)),
        (AF_INET6, ("::1", 0, 0, 0)),
    ),
)
class TestSlipRequestHandler:
    """Tests for SlipRequestHandler."""

    @pytest.fixture(autouse=True)
    def setup(self, family: int, address: TCPAddress) -> Generator[None, None, None]:
        """Prepare the test."""
        self.family = family
        self.bind_address = address
        # Cannot use standard TCPServer, because that is hardcoded to IPv4
        self.client_socket = socket(family=self.family)
        self.server_is_running = threading.Event()
        yield
        self.client_socket.close()

    def server(self, bind_address: TCPAddress, request_handler_class: type[SlipRequestHandler]) -> None:
        """Create a server."""
        srv = SlipServer(bind_address, request_handler_class)
        self.server_address = srv.server_address
        self.server_is_running.set()
        srv.handle_request()

    def test_working_of_sliprequesthandler(self) -> None:
        """Verify that the server returns the message with the bytes in reversed order."""
        server_thread = threading.Thread(target=self.server, args=(self.bind_address, DummySlipRequestHandler))
        server_thread.start()
        self.server_is_running.wait(0.5)
        self.client_socket.connect(self.server_address)
        self.client_socket.sendall(END + b"hallo" + END)
        response = self.client_socket.recv(4096)
        assert response == END + b"ollah" + END
        server_thread.join()
