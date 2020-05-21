#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
SlipRequestHandler
------------------

.. autoclass:: SlipRequestHandler
   :show-inheritance:

   The interface is identical to that offered by the
   :class:`socketserver.BaseRequestHandler` baseclass.
   To do anything useful, a derived class must define
   a new :meth:`handle` method, and may override any
   of the other methods.

   .. automethod:: setup
   .. automethod:: handle
   .. automethod:: finish
"""

from socketserver import BaseRequestHandler

from .slipsocket import SlipSocket


class SlipRequestHandler(BaseRequestHandler):
    """Base class for request handlers for SLIP-based communication

    This class is derived from :class:`socketserver.BaseRequestHandler`
    for the purpose of creating TCP server instances
    that can handle incoming SLIP-based connections.

    To implement a specific behaviour, all that
    is needed is to derive a class that
    defines a :meth:`handle` method that uses
    :attr:`self.request` to send and receive SLIP-encoded messages.
    """

    def setup(self) -> None:
        """Initializes the request handler.

        The original socket (available via :code:`self.request`)
        is wrapped in a :class:`SlipSocket` object.
        Derived classes may override this method,
        but should call ``super().setup()`` before
        accessing any :class:`SlipSocket`
        methods or attributes on :code:`self.request`.
        """
        if not isinstance(self.request, SlipSocket):
            # noinspection PyTypeChecker
            self.request = SlipSocket(self.request)

    def handle(self) -> None:
        """Services the request. Must be defined by a derived class.

        Note that in general it does not make sense
        to use a :class:`SlipRequestHandler` object
        to handle a single transmission, as is e.g. common with HTTP.
        The purpose of the SLIP protocol is to allow separation of
        messages in a continuous byte stream.
        As such, it is expected that the :meth:`handle` method of a derived class
        is capable of handling multiple SLIP messages:

        .. code::

            def handle(self):
                while True:
                    msg = self.request.recv_msg()
                    if msg == b'':
                        break
                    # Do something with the message
        """

    def finish(self) -> None:
        """Performs any cleanup actions.

        The default implementation does nothing.
        """
