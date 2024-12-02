# Copyright (c) 2024 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

from __future__ import annotations

import socket
from socketserver import TCPServer, UDPServer
from typing import TYPE_CHECKING, Generator, cast

import pytest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from sliplib.slipsocket import TCPAddress


from sliplib import SlipRequestHandler, SlipServer, SlipSocket


@pytest.fixture
def sock(mocker: MockerFixture) -> Generator[socket.socket, None, None]:
    address_family = socket.AF_INET
    mocked_socket = mocker.create_autospec(
        spec=socket.socket,
        instance=True,
        family=address_family,
        type=socket.SOCK_STREAM,
        proto=0,
    )
    yield mocked_socket
    mocked_socket.close()


@pytest.fixture
def slipsock(sock: socket.socket) -> SlipSocket:
    return SlipSocket(sock)


@pytest.fixture
def udpsock(mocker: MockerFixture) -> Generator[socket.socket, None, None]:
    address_family = socket.AF_INET
    mocked_socket = mocker.create_autospec(
        spec=socket.socket,
        instance=True,
        family=address_family,
        type=socket.SOCK_DGRAM,
        proto=0,
    )
    yield mocked_socket
    mocked_socket.close()


@pytest.fixture
def tcpserver(mocker: MockerFixture) -> TCPServer:
    return mocker.create_autospec(spec=TCPServer, instance=True, socket_type=socket.SOCK_STREAM)


@pytest.fixture
def udpserver(mocker: MockerFixture) -> UDPServer:
    return mocker.create_autospec(spec=UDPServer, instance=True, socket_type=socket.SOCK_DGRAM)


@pytest.fixture
def slipserver(mocker: MockerFixture) -> SlipServer:
    return mocker.create_autospec(spec=SlipServer, instance=True, socket_type=socket.SOCK_STREAM)


@pytest.fixture
def slip_request_handler(mocker: MockerFixture) -> SlipRequestHandler:
    return mocker.create_autospec(SlipRequestHandler, instance=True)


@pytest.fixture
def slip_request_handler_class(
    slip_request_handler: SlipRequestHandler, mocker: MockerFixture
) -> type[SlipRequestHandler]:
    return mocker.patch("sliplib.slipserver.SlipRequestHandler", autospec=True, return_value=slip_request_handler)


class TestSlipRequestHandler:
    def test_instantiate_with_regular_socket_and_tcpserver(self, sock: socket.socket, tcpserver: TCPServer) -> None:
        h = SlipRequestHandler(sock, ("93.184.216.34", 54321), tcpserver)
        assert isinstance(h.request, SlipSocket)
        assert h.request.socket is sock

    def test_instantiate_with_slip_socket_and_tcpserver(self, slipsock: SlipSocket, tcpserver: TCPServer) -> None:
        h = SlipRequestHandler(slipsock, ("93.184.216.34", 54321), tcpserver)
        assert h.request is slipsock

    def test_instantiate_with_regular_socket_and_slipserver(self, sock: socket.socket, slipserver: SlipServer) -> None:
        h = SlipRequestHandler(sock, ("93.184.216.34", 54321), slipserver)
        assert isinstance(h.request, SlipSocket)
        assert h.request.socket is sock

    def test_instantiate_with_slip_socket_and_slipserver(self, slipsock: SlipSocket, slipserver: SlipServer) -> None:
        h = SlipRequestHandler(slipsock, ("93.184.216.34", 54321), slipserver)
        assert h.request is slipsock

    def test_instantiate_with_udp_socket_fails(self, udpsock: socket.socket, tcpserver: TCPServer) -> None:
        with pytest.raises(ValueError, match="type SOCK_STREAM"):
            SlipRequestHandler(udpsock, ("93.184.216.34", 54321), tcpserver)

    def test_instantiate_with_udp_server_fails(self, sock: socket.socket, udpserver: UDPServer) -> None:
        with pytest.raises(TypeError):
            SlipRequestHandler(sock, ("93.184.216.34", 54321), udpserver)


@pytest.mark.parametrize(
    ("address", "family", "remote_address"),
    (
        (("127.0.0.1", 12345), socket.AF_INET, ("93.184.216.34", 54321)),
        (("::1", 12345, 0, 0), socket.AF_INET6, ("2606:2800:220:1:248:1893:25c8:1946", 54321)),
    ),
)
class TestSlipServer:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        address: TCPAddress,
        family: int,
        remote_address: TCPAddress,
        slip_request_handler: SlipRequestHandler,
        slip_request_handler_class: type[SlipRequestHandler],
        mocker: MockerFixture,
    ) -> Generator[None, None, None]:
        """Spy on the methods of the Request Handler."""
        self.slip_request_handler = slip_request_handler
        self.slip_request_handler_class = slip_request_handler_class
        self.address = address
        self.family = family
        self.remote_address = remote_address

        self.tcp_socket = mocker.create_autospec(
            spec=socket.socket, instance=True, type=socket.SOCK_STREAM, family=family
        )
        socketserver_socket = mocker.patch("socketserver.socket", autospec=True)
        socketserver_socket.socket.return_value = self.tcp_socket
        yield
        self.tcp_socket.close()

    def test_slipserver_instantiation(self) -> None:
        server = SlipServer(self.address, self.slip_request_handler_class)
        assert server.address_family == self.family
        assert isinstance(server.socket, SlipSocket)
        assert server.socket.socket is self.tcp_socket

    def test_slipserver_process_request(self, mocker: MockerFixture) -> None:
        server = SlipServer(self.address, self.slip_request_handler_class)
        handler_socket = mocker.create_autospec(
            spec=socket.socket,
            instance=True,
            family=self.family,
            type=socket.SOCK_STREAM,
        )
        handler_slip_socket = SlipSocket(handler_socket)
        server.process_request(cast(socket.socket, handler_slip_socket), self.remote_address)
        self.slip_request_handler_class.assert_called_once_with(handler_slip_socket, self.remote_address, server)  # type: ignore[attr-defined]
        handler_socket.close()
