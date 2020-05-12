#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

from socketserver import BaseRequestHandler

from .slipsocket import SlipSocket


class SlipRequestHandler(BaseRequestHandler):
    """Base class for request handlers for SLIP-based communication

    This class is derived from :class:`socketserver.BaseRequestHandler`
    for the purpose of creating TCP server instances
    that can handle incoming SLIP-based connections.

    This base class ensures that the connection
    is wrapped in a SlipSocket, and makes it
    available as :code:`self.request`.
    The original connection is still available as self.request.socket.
    The client address as available as :code:`self.client_address`,
    and the server as :code:`self.server`.

    To implement a specific behaviour, all that
    is needed is to derive a class that
    defines a :meth:`handle` method that uses
    :code:`self.request` to send and receive messages.

    Note that in general it does not make sense to use a :class:`SlipRequestHandler`
    to handle a single transmission, as is e.g. common with HTTP.
    The purpose of the SLIP protocol is to allow separation of
    data messages in a continuous byte stream.
    As such, it is expected that the :meth:`handle` method of a derived class
    is capable of handling multiple SLIP messages:

    .. code::

        class MySlipRequestHandler(SlipRequestHandler):
            ...
            def handle(self):
                while True:
                    msg = self.request.recv_msg()
                    if msg == b'':
                        break
                    # Do something with the message

    """

    def setup(self):
        if not isinstance(self.request, SlipSocket):
            # noinspection PyTypeChecker
            self.request = SlipSocket(self.request)
