# Copyright (c) 2024 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.


import socket
from socketserver import TCPServer
from typing import Generator, cast

import pytest
from pytest_mock import MockerFixture

from sliplib import SlipRequestHandler, SlipServer, SlipSocket


class TestSlipRequestHandler:
    @pytest.fixture(autouse=True)
    def setup(self, mocker: MockerFixture) -> Generator[None, None, None]:
        self.sock_mock = mocker.Mock(
            spec=socket.socket(socket.AF_INET),
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=0,
        )
        self.slipsocket = SlipSocket(self.sock_mock)
        self.server = mocker.Mock(spec=TCPServer)
        yield
        self.sock_mock.close()
        del self.slipsocket

    def test_instantiation_with_regular_socket(self) -> None:
        h = SlipRequestHandler(self.sock_mock, ("93.184.216.34", 54321), self.server)
        assert isinstance(h.request, SlipSocket)
        assert h.request.socket is self.sock_mock

    def test_instantiation_with_slip_socket(self) -> None:
        h = SlipRequestHandler(self.slipsocket, ("93.184.216.34", 54321), self.server)
        assert h.request is self.slipsocket


class TestSlipServer:
    @pytest.fixture(
        autouse=True,
        params=[
            (
                socket.AF_INET,
                ("93.184.216.34", 54321),  # example.com IPv4 address
                ("127.0.0.1", 12345),  # localhost IPv4 address
            ),
            (
                socket.AF_INET6,
                (
                    "2606:2800:220:1:248:1893:25c8:1946",
                    54321,
                    0,
                    0,
                ),  # example.com IPv6 address
                ("::1", 12345, 0, 0),  # localhost IPv6 address
            ),
        ],
    )
    def setup(self, request: pytest.FixtureRequest, mocker: MockerFixture) -> Generator[None, None, None]:
        """Prepare the test."""

        self.family, self.far_address, self.near_address = request.param
        self.sock_mock = mocker.Mock(
            spec=socket.socket(family=self.family),
            family=self.family,
            type=socket.SOCK_STREAM,
            proto=0,
        )
        self.slipsocket = SlipSocket(self.sock_mock)
        yield
        self.sock_mock.close()
        del self.slipsocket

    def test_slipserver_instantiation(self) -> None:
        server = SlipServer(self.near_address, SlipRequestHandler)
        assert isinstance(server.socket, SlipSocket)
        assert server.address_family == self.family

    def test_no_automatic_bind(self) -> None:
        server = SlipServer(self.near_address, SlipRequestHandler, bind_and_activate=False)
        assert not isinstance(server.socket, SlipSocket)
        slip_socket = SlipSocket(server.socket)
        server.socket = cast(socket.socket, slip_socket)
        server.server_bind()
        assert server.socket is cast(socket.socket, slip_socket)
