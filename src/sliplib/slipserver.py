#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
SlipRequestHandler
------------------

.. autoclass:: SlipRequestHandler
   :show-inheritance:

   .. automethod:: setup
   .. automethod:: handle
   .. automethod:: finish
"""
from __future__ import annotations

import socket
from socketserver import BaseRequestHandler, TCPServer
from typing import cast

from sliplib.slipsocket import SlipSocket, TCPAddress


class SlipRequestHandler(BaseRequestHandler):
    """Base class for request handlers for SLIP-based communication

    This class is derived from :class:`socketserver.BaseRequestHandler`
    for the purpose of creating TCP server instances
    that can handle incoming SLIP-based connections.

    To do anything useful, a derived class must define
    a new :meth:`handle` method that uses
    :attr:`self.request` to send and receive SLIP-encoded messages.

    Other methods can of course also be overridden if necessary.
    """

    def __init__(self, request: socket.socket | SlipSocket, client_address: TCPAddress, server: TCPServer):
        """Initializes the request handler.

        The type of the :arg:`request` parameter depends on the type of server
        that instantiates the request handler.
        If the server is a SlipServer, then :arg:`request` is a SlipSocket.
        Otherwise, it is a regular socket, and must be wrapped in a SlipSocket
        before it can be used.

        Args:
            request:
                The socket that is connected to the remote party.

            client_address:
                The remote TCP addresss.

            server:
                The TCPServer or SlipServer instance that instantiated this handler object.
        """
        if not isinstance(request, SlipSocket):
            request = SlipSocket(request)
        super().__init__(cast(socket.socket, request), client_address, server)

    def handle(self) -> None:
        """Services the request. Must be defined by a derived class.

        Note that in general it does not make sense
        to use a :class:`SlipRequestHandler` object
        to handle a single transmission, as is e.g. common with HTTP.
        The purpose of the SLIP protocol is to allow separation of
        messages in a continuous byte stream.
        As such, it is expected that the :meth:`handle` method of a derived class
        is capable of handling multiple SLIP messages, for example:

        .. code::

            def handle(self):
                while True:
                    msg = self.request.recv_msg()
                    if msg == b"":
                        break
                    # Do something with the message
        """

    def finish(self) -> None:
        """Performs any cleanup actions.

        The default implementation does nothing.
        """


class SlipServer(TCPServer):
    """Base class for SlipSocket based server classes."""

    def __init__(
        self,
        server_address: TCPAddress,
        handler_class: type[SlipRequestHandler],
        bind_and_activate: bool = True,  # noqa: FBT001 FBT002
    ):
        if self._is_ipv6_address(server_address):
            self.address_family = socket.AF_INET6
        super().__init__(server_address[0:2], handler_class, bind_and_activate)

    def server_bind(self) -> None:
        """Make the server socket into a SLIP socket and bind it to the server address."""
        if not isinstance(self.socket, SlipSocket):
            self.socket = cast(socket.socket, SlipSocket(self.socket))
        super().server_bind()

    @staticmethod
    def _is_ipv6_address(server_address: TCPAddress) -> bool:
        return ":" in server_address[0]
