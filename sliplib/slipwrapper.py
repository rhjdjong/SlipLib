# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import collections
import sys
from .slip import Driver, ProtocolError


class SlipWrapper:
    """Base class that provides a message based interface to a byte stream

    :class:`SlipWrapper` combines a :class:`Driver` instance with a byte stream.
    The :class:`SlipWrapper` class is an abstract base class.
    It offers the methods :meth:`send_msg` and :meth:`recv_msg` to send and
    receive single messages over the byte stream, but it does not of itself
    provide the means to interact with the stream.

    To interact with a concrete stream, a derived class must implement
    the methods :meth:`send_bytes` and :meth:`recv_bytes`
    to write to and read from the stream.
    """
    def __init__(self, stream):
        """
        To instantiate a :class:`SlipWrapper`, the user must provide
        an existing byte stream

        :param stream: the byte stream that will be wrapped..
        """
        self.stream = stream
        self.driver = Driver()
        self._messages = collections.deque()
        self._protocol_error = None
        self._traceback = None
        self._flush_needed = False
        self._stream_closed = False

    def send_bytes(self, packet):
        """Send a packet over the stream.

        Derived classes must override this method.

        :param bytes packet: the packet to send over the stream
        """
        raise NotImplementedError

    def recv_bytes(self):
        """Receive data from the stream.

        Derived classes must override this method.

        .. note::
            The convention used within the :class:`SlipWrapper` class
            is that :meth:`recv_bytes` returns an empty bytes object
            to indicate that the end of
            the byte stream has been reached, and no further data will
            be received. Derived implementations must ensure that
            this convention is followed.

        :return: bytes received from the stream
        :rtype: bytes
        """
        raise NotImplementedError

    def send_msg(self, message):
        """Send a SLIP-encoded message over the stream.

        :param bytes message: The message to encode and send
        """
        packet = self.driver.send(message)
        self.send_bytes(packet)

    def recv_msg(self):
        """Receive a single message from the stream.

        :return: A SLIP-decoded message
        :rtype: bytes
        :raises ProtocolError: when a SLIP protocol error has been encountered.
           A subsequent call to :meth:`recv_msg` (after handling the exception)
           will return the message from the next packet.
        """

        # First check if there are any pending messages
        if self._messages:
            return self._messages.popleft()

        # No pending messages left. If a ProtocolError has occurred
        # it must be re-raised here:
        if self._protocol_error:
            self._handle_pending_protocol_error()

        while not self._messages and not self._stream_closed:
            # As long as no messages are available,
            # flush the internal packet buffer,
            # and try to read data
            try:
                if self._flush_needed:
                    self._flush_needed = False
                    self._messages.extend(self.driver.flush())
                else:
                    data = self.recv_bytes()
                    if data == b'':
                        self._stream_closed = True
                    self._messages.extend(self.driver.receive(data))
            except ProtocolError as pe:
                self._messages.extend(self.driver.messages)
                self._protocol_error = pe
                self._traceback = sys.exc_info()[2]
                break

        if self._messages:
            return self._messages.popleft()

        if self._protocol_error:
            self._handle_pending_protocol_error()
        else:
            return b''

    def _handle_pending_protocol_error(self):
        try:
            raise self._protocol_error.with_traceback(self._traceback)
        finally:
            self._protocol_error = None
            self._traceback = None
            self._flush_needed = True
