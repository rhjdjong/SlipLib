#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
Module :mod:`~sliplib.slipserver`
=================================

The :mod:`~sliplib.slipserver` module contains the classes :class:`SlipRequestHandler` and :class:`SlipServer`,
that offer building blocks to create a SLIP server.

The :class:`SlipRequestHandler` and :class:`SlipServer` classes
can also be imported directly from the :mod:`sliplib` package.

.. autoclass:: SlipRequestHandler
   :show-inheritance:

   .. automethod:: handle
   .. automethod:: finish

.. autoclass:: SlipServer
   :show-inheritance:
"""

from __future__ import annotations

import socket
from socketserver import BaseRequestHandler, TCPServer
from typing import cast

from sliplib.slipsocket import SlipSocket, TCPAddress


class SlipRequestHandler(BaseRequestHandler):
    """Base class for request handlers for SLIP-based communication.

    This class is derived from :class:`socketserver.BaseRequestHandler`
    for the purpose of creating TCP server instances
    that can handle incoming SLIP-based connections.

    To do anything useful, a derived class must define
    its own :meth:`handle` method that uses
    :attr:`self.request` to send and receive SLIP-encoded messages.

    Other methods can of course also be overridden if necessary.
    """

    def __init__(self, request: socket.socket | SlipSocket, client_address: TCPAddress, server: TCPServer):
        """To initialize the request handler, a request, client address, and server instance must be provided.

        The type of the `request` parameter depends on the type of server
        that instantiates the request handler.
        If the server is a :class:`SlipServer`, then `request` is a :class:`~sliplib.slipsocket.SlipSocket` instance.
        Otherwise, it is a regular :class:`~socket.socket`,
        and the request handler wraps it in a :class:`~sliplib.slipsocket.SlipSocket` instance.

        .. Note::

           If `request` is not a :class:`~sliplib.slipsocket.SlipSocket` instance (as will happen when
           `server` is not a :class:`SlipServer` instance),
           the behavior of the wrapped :class:`~sliplib.slipsocket.SlipSocket` instance
           with respect to sending a leading :const:`~sliplib.slip.config.END` byte is determined
           by the value of :attr:`~sliplib.slip.config.USE_LEADING_END_BYTE`
           at the time the request handler is initialized.

        Args:
            request:
                The socket that is connected to the remote party.

            client_address (:class:`~sliplib.slipsocket.TCPAddress`)::
                The remote TCP address.

            server:
                The server instance that instantiated this handler object.
        """
        if server.socket_type != socket.SOCK_STREAM:
            message = (
                f"{self.__class__.__name__} instance can only be used "
                f"with a TCP server (got {server.__class__.__name__})"
            )
            raise TypeError(message)

        if not isinstance(request, SlipSocket):
            request = SlipSocket(request)
        super().__init__(cast(socket.socket, request), client_address, server)

    def handle(self) -> None:
        """Service the request. Must be defined by a derived class.

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
        """Perform any cleanup actions.

        The default implementation does nothing.
        """


class SlipServer(TCPServer):
    """Base class for SlipSocket based server classes.

    This is a convenience class, that offers a few enhancements
    over the regular :external:class:`~socketserver.TCPServer` from the standard library.

     * It uses the supplied `server_address` to determine if it must use an IPv4 or IPv6 socket.
       The class :external:class:`~socketserver.TCPServer` on the other hand is hardcoded to use only IPv4 addresses,
       and must be subclassed in order to use IPv6 addresses.
     * The socket that is passed to the `handler_class` instance is a :class:`~sliplib.slipsocket.SlipSocket` instance
       with the same leading-end-byte behavior as the server socket.
       That avoids ambiguity when :data:`config.USE_LEADING_END_BYTE <sliplib.slip.config.USE_LEADING_END_BYTE>`
       may have been modified.
    """

    def __init__(
        self,
        server_address: TCPAddress,
        handler_class: type[SlipRequestHandler],
        bind_and_activate: bool = True,  # noqa: FBT001 FBT002
    ):
        """
        Args:
            server_address (:class:`~sliplib.slipsocket.TCPAddress`): The address on which the server listens.
            handler_class: The class that will be instantiated to handle an incoming request.
            bind_and_activate: Flag to indicate if the server must be bound and activated at creation time.
        """
        if self._is_ipv6_address(server_address):
            self.address_family = socket.AF_INET6
        super().__init__(server_address[0:2], handler_class, bind_and_activate)
        self.socket = cast(socket.socket, SlipSocket(self.socket))

    @staticmethod
    def _is_ipv6_address(server_address: TCPAddress) -> bool:
        return ":" in server_address[0]
