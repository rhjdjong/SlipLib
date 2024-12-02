#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
Constants
---------

The following constants represent the special bytes
used by SLIP for delimiting and encoding messages.

.. autovariable:: END
   :no-type:
.. autovariable:: ESC
   :no-type:
.. autovariable:: ESC_END
   :no-type:
.. autovariable:: ESC_ESC
   :no-type:


Functions
---------

The following are lower-level functions, that should normally not be used directly.

.. autofunction:: encode
.. autofunction:: decode
.. autofunction:: is_valid

Classes
-------

.. autoclass:: Driver

   Class :class:`Driver` offers the following methods:

   .. automethod:: send
   .. automethod:: get
   .. automethod:: receive

"""

from __future__ import annotations

import re
from queue import Empty, Queue

END = b"\xc0"  #: The SLIP `END` byte.
ESC = b"\xdb"  #: The SLIP `ESC` byte.
ESC_END = b"\xdc"  #: The SLIP byte that, when preceded by an `ESC` byte, represents an escaped `END` byte.
ESC_ESC = b"\xdd"  #: The SLIP byte that, when preceded by an `ESC` byte, represents an escaped `ESC` byte.


class ProtocolError(ValueError):
    """Exception to indicate that a SLIP protocol error has occurred.

    This exception is raised when an attempt is made to decode
    a packet with an invalid byte sequence.
    An invalid byte sequence is either an :const:`ESC` byte followed
    by any byte that is not an :const:`ESC_ESC` or :const:`ESC_END` byte,
    or a trailing :const:`ESC` byte as last byte of the packet.

    The :exc:`ProtocolError` carries the invalid packet
    as the first (and only) element in in its :attr:`args` tuple.
    """


def encode(msg: bytes) -> bytes:
    """Encodes a message (a byte sequence) into a SLIP-encoded packet.

    Args:
        msg: The message that must be encoded

    Returns:
        The SLIP-encoded message
    """
    msg = bytes(msg)
    return END + msg.replace(ESC, ESC + ESC_ESC).replace(END, ESC + ESC_END) + END


def decode(packet: bytes) -> bytes:
    """Retrieves the message from the SLIP-encoded packet.

    Args:
        packet: The SLIP-encoded message.
           Note that this must be exactly one complete packet.
           The :func:`decode` function does not provide any buffering
           for incomplete packages, nor does it provide support
           for decoding data with multiple packets.
    Returns:
        The decoded message

    Raises:
        ProtocolError: if the packet contains an invalid byte sequence.
    """
    if not is_valid(packet):
        raise ProtocolError(packet)
    return packet.strip(END).replace(ESC + ESC_END, END).replace(ESC + ESC_ESC, ESC)


def is_valid(packet: bytes) -> bool:
    """Indicates if the packet's contents conform to the SLIP specification.

    A packet is valid if:

    * It contains no :const:`END` bytes other than leading and/or trailing :const:`END` bytes, and
    * Each :const:`ESC` byte is followed by either an :const:`ESC_END` or an :const:`ESC_ESC` byte.

    Args:
        packet: The packet to inspect.

    Returns:
        :const:`True` if the packet is valid, :const:`False` otherwise
    """
    packet = packet.strip(END)
    return not (END in packet or packet.endswith(ESC) or re.search(ESC + b"[^" + ESC_END + ESC_ESC + b"]", packet))


class Driver:
    """Class to handle the SLIP-encoding and decoding of messages

    This class manages the handling of encoding and decoding of
    messages according to the SLIP protocol.
    """

    def __init__(self) -> None:
        self._finished = False
        self._recv_buffer = b""
        self._packets: Queue[bytes] = Queue()

    def send(self, message: bytes) -> bytes:
        """Encodes a message into a SLIP-encoded packet.

        The message can be any arbitrary byte sequence.

        Args:
            message: The message that must be encoded.

        Returns:
            A packet with the SLIP-encoded message.
        """
        return encode(message)

    def receive(self, data: bytes | int) -> None:
        """Decodes data to extract the SLIP-encoded messages.

        Processes :obj:`data`, which must be a bytes-like object,
        and extracts and buffers the SLIP messages contained therein.

        A non-terminated SLIP packet in :obj:`data`
        is also buffered, and processed with the next call to :meth:`receive`.

        Args:
            data: A bytes-like object to be processed.

                An empty :obj:`data` parameter indicates that no more data will follow.

                To accommodate iteration over byte sequences, an
                integer in the range(0, 256) is also accepted.

        Returns:
            None.

        .. versionchanged:: 0.7
           `receive()` no longer returns a list of decoded messages.
        """

        # When a single byte is fed into this function
        # it is received as an integer, not as a bytes object.
        # It must first be converted into a bytes object.
        if isinstance(data, int):
            data = bytes((data,))

        # Empty data indicates that the data reception is complete.
        # To force a buffer flush, an END byte is added, so that the
        # current contents of _recv_buffer will form a complete message.
        if not data:
            self._finished = True
            data = END

        self._recv_buffer += data

        # The following situations can occur:
        #
        #  1) _recv_buffer is empty or contains only END bytes --> no packets available
        #  2) _recv_buffer contains non-END bytes --> one or more (partial) packets are available
        #
        # Strip leading END bytes from _recv_buffer to avoid handling empty packets.
        self._recv_buffer = self._recv_buffer.lstrip(END)

        # The _recv_buffer is now split on sequences of one or more END bytes.
        # The trailing element from the split operation is a possibly incomplete
        # packet; this element is therefore used as the new _recv_buffer.
        # If _recv_buffer contains one or more trailing END bytes,
        # (meaning that there are no incomplete packets), then the last element,
        # and therefore the new _recv_buffer, is an empty bytes object.
        *new_packets, self._recv_buffer = re.split(END + b"+", self._recv_buffer)

        # Add the packets to the buffer
        for packet in new_packets:
            self._packets.put(packet)

    def get(self, *, block: bool = True, timeout: float | None = None) -> bytes | None:
        """Get the next decoded message.

        Remove and decode a SLIP packet from the internal buffer, and return the resulting message.
        If `block` is `True` and `timeout` is `None`(the default), then this method blocks until a message is available.
        If `timeout` is a positive number, the blocking will last for at most `timeout` seconds,
        and the method will return `None` if no message became available in that time.
        If `block` is `False` the method returns immediately with either a message or `None`.

        Returns:
            A decoded SLIP message, or an empty bytestring `b""` if no further message will come available.

        Raises:
            ProtocolError: When the packet that contained the message had an invalid byte sequence.

        .. versionadded:: 0.7
        """
        try:
            packet = self._packets.get(block, timeout)
        except Empty:
            return b"" if self._finished else None

        return decode(packet)
