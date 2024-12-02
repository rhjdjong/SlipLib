#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
SlipStream
----------
.. autoprotocol:: IOStream
   :show-inheritance:

.. autoclass:: SlipStream(stream, [chunk_size])
   :show-inheritance:

   A :class:`SlipStream` instance has the following attributes in addition to the attributes
   offered by its base class :class:`SlipWrapper`:

   .. autoattribute:: chunk_size
   .. autoattribute:: readable
   .. autoattribute:: writable
"""

from __future__ import annotations

import io
import warnings
from typing import Any, Protocol

from sliplib.slipwrapper import SlipWrapper


class IOStream(Protocol):
    """
    Protocol class for wrappable byte streams.

    Any object that produces and consumes a byte stream and contains the two required methods can be used.
    Typically, an IOStream is a subclass of :class:`io.RawIOBase`, :class:`io.BufferedIOBase`,
    :class:`io.FileIO`, or similar classes, but this is not required.
    """

    def read(self, chunksize: int) -> bytes:
        """Read `chunksize` bytes from the stream

        Args:
            chunksize: The number of bytes to read from the :protocol:`IOStream`.

        Returns:
            The bytes read from the :protocol:`IOStream`. May be less than the number
            specified by `chunksize`.
        """

    def write(self, data: bytes) -> int:
        """Write data to the stream.

        Args:
            data: The bytes to write on to `IOStream`.

        Returns:
            The number of bytes actually written. This may be less than the
            number of bytes contained in `data`.
        """


class SlipStream(SlipWrapper[IOStream]):
    """Class that wraps an IO stream with a :class:`Driver`

    :class:`SlipStream` combines a :class:`Driver` instance with a concrete byte stream.
    The byte stream must support the methods :meth:`read` and :meth:`write`.
    To avoid conflicts and ambiguities caused by different `newline` conventions,
    streams that have an :attr:`encoding` attribute
    (such as :class:`io.StringIO` objects, or text files that are not opened in binary mode)
    are not accepted as a byte stream.

    The :class:`SlipStream` class has all the methods and attributes
    from its base class :class:`SlipWrapper`.
    In addition, it directly exposes all methods and attributes of
    the contained :obj:`stream`, except for the following:

     * :meth:`read*` and :meth:`write*`. These methods are not
       supported, because byte-oriented read and write operations
       would invalidate the internal state maintained by :class:`SlipStream`.
     * Similarly, :meth:`seek`, :meth:`tell`, and :meth:`truncate` are not supported,
       because repositioning or truncating the stream would invalidate the internal state.
     * :meth:`raw`, :meth:`detach` and other methods that provide access to or manipulate
       the stream's internal data.

    Instead of the :meth:`read*` and :meth:`write*` methods
    a :class:`SlipStream` object provides the method :meth:`recv_msg` and :meth:`send_msg`
    to read and write SLIP-encoded messages.

    .. deprecated:: 0.6
       Direct access to the methods and attributes of the contained :obj:`stream`
       will be removed in version 1.0

    """

    def __init__(self, stream: IOStream, chunk_size: int = io.DEFAULT_BUFFER_SIZE):
        """
        To instantiate a :class:`SlipStream` object, the user must provide
        a pre-constructed open byte stream that is ready for reading and/or writing

        Args:
            stream: The byte stream that will be wrapped.

            chunk_size: The number of bytes to read per read operation.
                The default value for `chunck_size` is `io.DEFAULT_BUFFER_SIZE`.

                Setting the `chunk_size` is useful when the stream has a low bandwidth
                and/or bursty data (e.g. a serial port interface).
                In such cases it is useful to have a `chunk_size` of 1, to avoid that the application
                hangs or becomes unresponsive.

        .. versionadded:: 0.6
           The `chunk_size` parameter.

        A :class:`SlipStream` instance can e.g. be useful to read slip-encoded messages
        from a file:

        .. code::

            with open('/path/to/a/slip/encoded/file', mode='rb') as f:
                slip_file = SlipStream(f)
                for msg in slip_file:
                    # Do something with the message

        """
        for method in ("read", "write"):
            if not hasattr(stream, method) or not callable(getattr(stream, method)):
                error_msg = f"{stream.__class__.__name__} object has no method {method}"
                raise TypeError(error_msg)
        if hasattr(stream, "encoding"):
            error_msg = f"{stream.__class__.__name__} object is not a byte stream"
            raise TypeError(error_msg)

        #: The number of bytes to read during each read operation.
        self.chunk_size = chunk_size if chunk_size > 0 else io.DEFAULT_BUFFER_SIZE

        super().__init__(stream)

    def send_bytes(self, packet: bytes) -> None:
        """See base class"""
        while packet:
            number_of_bytes_written = self.stream.write(packet)
            packet = packet[number_of_bytes_written:]

    def recv_bytes(self) -> bytes:
        """See base class"""
        return b"" if self._stream_is_closed else self.stream.read(self.chunk_size)

    @property
    def readable(self) -> bool:
        """Indicates if the wrapped stream is readable.
        The value is `True` if the readability of the wrapped stream
        cannot be determined.
        """
        return getattr(self.stream, "readable", True)

    @property
    def writable(self) -> bool:
        """Indicates if the wrapped stream is writable.
        The value is `True` if the writabilty of the wrapped stream
        cannot be determined.
        """
        return getattr(self.stream, "writable", True)

    @property
    def _stream_is_closed(self) -> bool:
        """Indicates if the wrapped stream is closed.
        The value is `False` if it cannot be determined if the wrapped stream is closed.
        """
        return getattr(self.stream, "closed", False)

    def __getattr__(self, attribute: str) -> Any:
        if attribute.startswith(("read", "write")) or attribute in (
            "detach",
            "flushInput",
            "flushOutput",
            "getbuffer",
            "getvalue",
            "peek",
            "raw",
            "reset_input_buffer",
            "reset_output_buffer",
            "seek",
            "seekable",
            "tell",
            "truncate",
        ):
            error_msg = f"'{self.__class__.__name__}' object has no attribute '{attribute}'"
            raise AttributeError(error_msg)

        # Deprecation warning
        warning_msg = "Direct access to the enclosed stream attributes and methods will be removed in version 1.0"
        warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)

        return getattr(self.stream, attribute)
