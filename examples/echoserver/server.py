# ruff: noqa: T201

# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

"""
Server
++++++

The :file:`server.py` example file is a demonstrator echo server.

Usage:
  python echoserver.py [ipv6]

The program uses a subclass of :class:`~sliplib.slipserver.SlipRequestHandler`
that transforms the :attr:`request` attribute into
a dedicated :class:`~sliplib.slipsocket.SlipSocket` subclass that prints
the raw data that is received and sent.
The request handler prints the decoded message,
and then reverses the order of the bytes in the encoded message
(so ``abc`` becomes ``cba``), before sending it back to the client.
"""

from __future__ import annotations

import socket
import sys
from socketserver import TCPServer
from typing import Any

from sliplib import SlipRequestHandler, SlipSocket


class _ChattySocket(SlipSocket):
    """A :class:`~sliplib.slipsocket.SlipSocket` subclass that prints the raw data that is received and sent."""

    def recv_bytes(self) -> bytes:
        data = super().recv_bytes()
        print("Raw data received:", data)
        return data

    def send_bytes(self, data: bytes) -> None:
        print("Sending raw data:", data)
        super().send_bytes(data)


class SlipHandler(SlipRequestHandler):
    """A :class:`~sliplib.slipserver.SlipRequestHandler` that reverses and echoes the received message."""

    def __init__(self, request: socket.socket | SlipSocket, *args: Any) -> None:
        if isinstance(request, SlipSocket):
            request.__class__ = _ChattySocket
        else:
            request = _ChattySocket(request)
        print(f"Incoming connection from {request.getpeername()}")
        super().__init__(request, *args)

    # Dedicated handler to show the encoded bytes.
    def handle(self) -> None:
        while True:
            message = self.request.recv_msg()
            print("Decoded data:", message)
            if message:
                self.request.send_msg(bytes(reversed(message)))
            else:
                print("Closing down")
                break


class TCPServerIPv6(TCPServer):
    """An IPv6 TCPServer"""

    address_family = socket.AF_INET6


def main() -> None:
    hostname, server_class = ("::1", TCPServerIPv6) if len(sys.argv) > 1 else ("127.0.0.1", TCPServer)
    server = server_class((hostname, 0), SlipHandler)
    print(f"Slip server listening on {hostname}, port", server.server_address[1])
    server.handle_request()


if __name__ == "__main__":
    main()
