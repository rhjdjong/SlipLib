#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
Module :mod:`~sliplib.slip`
===========================

The :mod:`~sliplib.slip` module contains configuration settings and
lower-level functions and classes that are mainly useful for extending the :mod:`sliplib` package.

The configuration settings, functions, classes, and exception in this module can also be imported directly from the
:mod:`sliplib` package.

Configuration
-------------

.. attribute:: config

   The configuration settings are stored in the :attr:`config` configuration object.
   The :attr:`config` object provides constants, configuration settings, and a context manager
   for :mod:`sliplib`.


   Constants
   +++++++++

   .. autoattribute:: config.END

      The SLIP :const:`~config.END` byte. Used to delimit SLIP packages.

   .. autoattribute:: config.ESC

      The SLIP :const:`~config.ESC` byte.
      Used to escape :const:`~config.ESC` and :const:`~config.END` bytes in the message.

   .. autoattribute:: config.ESC_END

      The escaped value of an :const:`~config.END` byte.

   .. autoattribute:: config.ESC_ESC

      The escaped value of an :const:`~config.ESC` byte.

   For backwards compatibility reasons these constants can also be imported directly
   from the top-level :mod:`sliplib` module.

   Settings
   ++++++++

   .. autoattribute:: config.USE_LEADING_END_BYTE

      Indicates if a leading :const:`~config.END` byte must be sent.

   Context Manager
   +++++++++++++++

   .. automethod:: config.use_leading_end_byte(value)

The :obj:`config` configuration object and its constants
:const:`~config.END`, :const:`~config.ESC`, :const:`~config.ESC_END`, and :const:`~config.ESC_ESC`,
as well as the :func:`~config.use_leading_end_byte` context manager
can also be imported directly from the :mod:`sliplib` module.

Functions
---------

The following are lower-level functions that should normally not be used directly.

.. autofunction:: encode
.. autofunction:: decode
.. autofunction:: is_valid

Classes
-------

.. autoclass:: Driver

   Class :class:`Driver` offers the following methods:

   .. automethod:: send
   .. automethod:: receive
   .. automethod:: get
   .. autoproperty:: sends_leading_end_byte

Exceptions
----------

.. autoexception:: ProtocolError

"""

from __future__ import annotations

import re
from collections.abc import Iterator  # noqa: TCH003
from contextlib import contextmanager
from queue import Empty, Queue
from threading import RLock
from typing import Final


class _Configuration:
    """Configuration object for sliplib."""

    _END: Final = b"\xc0"
    _ESC: Final = b"\xdb"
    _ESC_END: Final = b"\xdc"
    _ESC_ESC: Final = b"\xdd"

    #: Indicates if a leading :const:`~config.END` byte must be sent.
    _USE_LEADING_END_BYTE = False

    _use_leading_end_byte_lock: RLock = RLock()

    #: The SLIP :const:`~config.END` byte. Used to delimit SLIP packages.
    @property
    def END(self) -> bytes:  # noqa: N802
        """The SLIP :const:`~config.END` byte. Used to delimit SLIP packages."""
        return self._END

    @property
    def ESC(self) -> bytes:  # noqa: N802
        """The SLIP :const:`~config.ESC` byte.
        Used to escape :const:`~config.ESC` and :const:`~config.END` bytes in the message."""
        return self._ESC

    @property
    #: The escaped value of an :const:`~config.END` byte.
    def ESC_END(self) -> bytes:  # noqa: N802
        """#: The escaped value of an :const:`~config.END` byte."""
        return self._ESC_END

    @property
    def ESC_ESC(self) -> bytes:  # noqa: N802
        """The escaped value of an :const:`~config.ESC` byte."""
        return self._ESC_ESC

    @property
    def USE_LEADING_END_BYTE(self) -> bool:  # noqa: N802
        """Indicates if a leading :const:`~config.END` byte must be sent."""
        return self._USE_LEADING_END_BYTE

    @USE_LEADING_END_BYTE.setter
    def USE_LEADING_END_BYTE(self, value: bool) -> None:  # noqa: N802
        with self._use_leading_end_byte_lock:
            self._USE_LEADING_END_BYTE = value

    @contextmanager
    def use_leading_end_byte(self, value: bool) -> Iterator[None]:  # noqa: FBT001
        """Temporarily modify the value of :data:`USE_LEADING_END_BYTE`.

        This context manager ensures that any :class:`~sliplib.slip.Driver`
        and :class:`~sliplib.slipwrapper.SlipWrapper` instances that are
        defined in its body use a specific value for :data:`USE_LEADING_END_BYTE`.
        This is particularly useful when the application interacts with different endpoints,
        some that require a leading :const:`~config.END` byte,
        and others that cannot handle multiple subsequent :const:`~config.END` bytes.
        By using this context manager, the order of the creation of the instances can be modified
        without having to worry about the current value of :data:`USE_LEADING_END_BYTE`.
        Example:

        .. code-block:: python

            with use_leading_end_byte(True):
                slip_socket = SlipSocket(sock)  # Where sock is a previously created socket.
            # Calling `slip_socket.send_msg(message)` will send the encoded message
            # with both a leading and trailing END byte.

        .. versionadded:: 0.7.0

        .. note::

           The temporary value of :data:`USE_LEADING_END_BYTE` does not propagate to processes
           that are created or started in the body of the context manager.

        .. warning::

           :data:`USE_LEADING_END_BYTE` is a global setting.
           For that reason, the temporary value of :data:`USE_LEADING_END_BYTE` is
           protected from modification by other threads.
           This means that inside the body of this context manager, you should e.g. not wait for notifications from
           another thread when that other thread also uses this context manager.
           As an example, the following will deadlock because the spawned thread will never
           enter the body of the context manager.

           .. code-block:: python

               def make_server(address, handler_class, event):
                   with config.use_leading_end_byte(False):
                       slip_server = SlipServer(address, handler_class)
                       slip_server.handle_request()
                   event.set()


               with config.use_leading_end_byte(True):
                   event = threading.Event()
                   server_thread = threading.Thread(
                       target=self.server,
                       args=(address, SlipRequestHandler, event),
                   )
                   server_thread.start()
                   event.wait()
                   client = SlipSocket.make_client(address)

           As a general rule, the body of the context manager should only contain statements
           that directly create :class:`~sliplib.slip.Driver`
           and/or :class:`~sliplib.slipwrapper.SlipWrapper` instances.
           The above example should be rewritten to something like:

           .. code-block:: python

               def make_server(address, handler_class, event):
                   with config.use_leading_end_byte(False):
                       slip_server = SlipServer(address, handler_class)
                   slip_server.handle_request()
                   event.set()


               event = threading.Event()
               server_thread = threading.Thread(
                   target=self.server,
                   args=(address, SlipRequestHandler, event),
               )
               server_thread.start()
               event.wait()
               with config.use_leading_end_byte(True):
                   client = SlipSocket.make_client(address)

        Args:
            value: The temporary value of :data:`USE_LEADING_END_BYTE`.

        :rtype: :external:obj:`~typing.ContextManager` [:external:obj:`None`]
        """
        with self._use_leading_end_byte_lock:
            current_value = self.USE_LEADING_END_BYTE
            try:
                self.USE_LEADING_END_BYTE = value
                yield
            finally:
                self.USE_LEADING_END_BYTE = current_value


config = _Configuration()

END = config.END
ESC = config.ESC
ESC_END = config.ESC_END
ESC_ESC = config.ESC_ESC

use_leading_end_byte = config.use_leading_end_byte


class ProtocolError(ValueError):
    """Exception to indicate that a SLIP protocol error has occurred.

    This exception is raised when an attempt is made to decode
    a packet with invalid bytes or byte sequences.
    Invalid bytes are :const:`~config.END` bytes or a trailing :const:`~config.ESC` byte.
    An invalid byte sequence is an :const:`~config.ESC` byte followed
    by any byte that is not an :const:`~config.ESC_ESC` or :const:`~config.ESC_END` byte.

    The :exc:`ProtocolError` carries the invalid packet
    as the first (and only) element in its :attr:`args` tuple.
    """


def encode(msg: bytes) -> bytes:
    """Encode a message (a byte sequence) into a SLIP-encoded packet.

    This function replaces any :const:`~config.END` or :const:`~config.ESC` byte
    in the message with their SLIP-escaped value.

    Args:
        msg: The message that must be encoded

    Returns:
        The SLIP-encoded message

    .. versionchanged:: 0.7.0
       Leading and/or trailing :const:`~config.END` bytes are no longer included in the return value.
       As of version 0.7.1, the original version of the :func:`~sliplib.legacy.encode()` function is available in the
       :mod:`~sliplib.legacy` module.
    """
    msg = bytes(msg)
    return msg.replace(ESC, ESC + ESC_ESC).replace(END, ESC + ESC_END)


def decode(packet: bytes) -> bytes:
    """Retrieve the message from the SLIP-encoded packet.

    This function replaces any escaped SLIP bytes with their original values

    Args:
        packet: The SLIP-encoded message.
           Note that this must be exactly one complete packet,
           without any leading and/or trailing :const:`~config.END` bytes.
           The :func:`decode` function does not provide any buffering
           for incomplete packages, nor does it provide support
           for decoding data with multiple packets.
    Returns:
        The decoded message

    Raises:
        ProtocolError: if the packet contains an invalid byte sequence.

    .. versionchanged:: 0.7.0
       Leading and/or trailing :const:`~config.END` bytes are no longer allowed.
       As of version 0.7.1, the original version of the :func:`~sliplib.legacy.decode()` function is available in the
       :mod:`~sliplib.legacy` module.

    """
    if not is_valid(packet):
        raise ProtocolError(packet)
    return packet.replace(ESC + ESC_END, END).replace(ESC + ESC_ESC, ESC)


def is_valid(packet: bytes) -> bool:
    """Indicate if the packet's contents conform to the SLIP specification.

    A packet is valid if:

    * It contains no :const:`~config.END` bytes, and
    * Each :const:`~config.ESC` byte is followed by either
      an :const:`~config.ESC_END` or an :const:`~config.ESC_ESC` byte.

    Args:
        packet: The packet to inspect.

    Returns:
        :external:obj:`True` if the packet is valid, :external:obj:`False` otherwise

    .. versionchanged:: 0.7.0
       Leading and/or trailing :const:`~config.END` bytes are no longer allowed.
    """
    return not (END in packet or packet.endswith(ESC) or re.search(ESC + b"[^" + ESC_END + ESC_ESC + b"]", packet))


class Driver:
    """Handle the SLIP-encoding and decoding of messages."""

    def __init__(self) -> None:
        self._prefix = END if config.USE_LEADING_END_BYTE else b""
        self._finished = False
        self._recv_buffer = b""
        self._packets: Queue[bytes] = Queue()

    def send(self, message: bytes) -> bytes:
        """Encode a message into a SLIP-encoded packet.

        The message can be any arbitrary byte sequence.

        Args:
            message: The message that must be encoded.

        Returns:
            A packet with the SLIP-encoded message, including any required
            leading and trailing :const:`~config.END` bytes.
        """
        return self._prefix + encode(message) + END

    def receive(self, data: bytes | int) -> None:
        """Extract and buffer SLIP packets.

        Processes `data`, which must be a bytes-like object,
        and extracts and buffers the SLIP packets contained therein.

        A non-terminated SLIP packet in `data`
        is also buffered, and extended with the next call to :meth:`receive`.

        Args:
            data: A bytes-like object to be processed.

                An empty `data` parameter indicates that no more data will follow.

                To accommodate iteration over byte sequences, an
                integer in the range(0, 256) is also accepted.

        Returns:
            :external:obj:`None`:

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
        If `block` is :external:obj:`True` and `timeout` is :external:obj:`None` (the default),
        then this method blocks until a message is available.
        If `timeout` is a positive number, the blocking will last for at most `timeout` seconds,
        and the method will return :external:obj:`None` if no message became available in that time.
        If `block` is :external:obj:`False`,
        the method returns immediately with either a message or :external:obj:`None`.

        Note:
            `block` and `timeout` are keyword-only parameters.

        Args:
            block: If :external:obj:`True`, then block for at most timeout seconds. Otherwise, return immediately.
            timeout: The number of seconds to wait for a message to become available.

        Returns:
            - :external:obj:`None` if no message is available,
            - a decoded SLIP message, or
            - an empty bytestring :obj:`b""` if no further messages will come available.

        Raises:
            ProtocolError: When the packet that contained the message had an invalid byte sequence.

        .. versionadded:: 0.7
        """
        try:
            packet = self._packets.get(block, timeout)
        except Empty:
            return b"" if self._finished else None

        return decode(packet)

    @property
    def sends_leading_end_byte(self) -> bool:
        """Indicates whether this :class:`Driver` instance sends a leading :const:`~config.END` byte.

        .. versionadded:: 0.7.0
        """
        return self._prefix == END
