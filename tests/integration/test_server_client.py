#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

# ruff: noqa: UP006 UP035

"""
This module tests SlipSocket using a SLIP echo server, similar to the one in the examples directory.
"""

import socket
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from socketserver import TCPServer
from typing import Generator, Mapping, Tuple, Type

import pytest

from sliplib import SlipRequestHandler, SlipSocket
from sliplib.slipsocket import TCPAddress


class SlipEchoHandler(SlipRequestHandler):
    """SLIP request handler that echoes the received message, but with the bytes in reversed order."""

    def handle(self) -> None:
        while True:
            message = self.request.recv_msg()
            if not message:
                break
            # Reverse the order of the bytes and send it back.
            data_to_send = bytes(reversed(message))
            self.request.send_msg(data_to_send)


class SlipEchoServer:
    """Execution helper for the echo server. Sends the server address back over the pipe."""

    server_data: Mapping[int, Tuple[Type[TCPServer], str]] = {
        socket.AF_INET: (TCPServer, "127.0.0.1"),
        socket.AF_INET6: (
            type("TCPServerIPv6", (TCPServer,), {"address_family": socket.AF_INET6}),
            "::1",
        ),
    }

    def __init__(self, address_family: int, pipe: Connection) -> None:
        server_class, localhost = self.server_data[address_family]
        self.server = server_class((localhost, 0), SlipEchoHandler)
        pipe.send(self.server.server_address)
        self.server.handle_request()


class SlipEchoClient:
    """Client for the SLIP echo server"""

    def __init__(self, address: TCPAddress) -> None:
        self.sock = SlipSocket.create_connection(address)

    def echo(self, msg: bytes) -> bytes:
        """Send message to the SLIP server and returns the response."""
        self.sock.send_msg(msg)
        return self.sock.recv_msg()

    def close(self) -> None:
        """Close the SLIP socket"""
        self.sock.close()


class TestEchoServer:
    """Test for the SLIP echo server"""

    @pytest.fixture(autouse=True, params=[socket.AF_INET, socket.AF_INET6])
    def setup(self, request: pytest.FixtureRequest, capfd: pytest.CaptureFixture[str]) -> Generator[None, None, None]:
        """Prepare the server and client"""
        near, far = Pipe()
        address_family = request.param
        self.server = Process(target=SlipEchoServer, args=(address_family, far))
        self.server.start()
        address_available = near.poll(1.5)  # AppVeyor sometimes takes a long time to run the server.
        if address_available:
            server_address = near.recv()
        else:
            captured = capfd.readouterr()
            pytest.fail(captured.err)
        self.client = SlipEchoClient(server_address)
        yield
        self.client.close()
        self.server.join()

    def test_echo_server(self) -> None:
        """Test the echo server"""
        data = [(b"hallo", b"ollah"), (b"goodbye", b"eybdoog")]
        for snd_msg, expected_reply in data:
            assert self.client.echo(snd_msg) == expected_reply
