#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
SlipStream
----------

.. autoclass:: SlipStream(stream, [chunk_size])
   :show-inheritance:

   A :class:`SlipStream` instance has the following attributes in addition to the attributes
   offered by its base class :class:`SlipWrapper`:

   .. autoattribute:: readable
   .. autoattribute:: writable
"""
from __future__ import annotations

import io
import warnings
from typing import Any, Protocol

from .slipwrapper import SlipWrapper


class _ProtoStream(Protocol):
    """Protocol class for wrappable streams"""

    def read(self, chunksize: int) -> bytes:
        """Read `chunksize` bytes from the stream"""

    def write(self, data: bytes) -> int:
        """Write data to the stream."""


class SlipStream(SlipWrapper[_ProtoStream]):
    """Class that wraps an IO stream with a :class:`Driver`

    :class:`SlipStream` combines a :class:`Driver` instance with a concrete byte stream.
    The byte stream must support the methods :meth:`read` and :meth:`write`.
    To avoid conflicts and ambiguities caused by different `newline` conventions,
    streams that have an :attr:`encoding` attribute
    (such as :class:`io.StringIO` objects, or text files that are not opened in binary mode)
    are not accepted as a byte stream.

    The :class:`SlipStream` class has all the methods and attributes
    from its base class :class:`SlipWrapper`.
    In addition it directly exposes all methods and attributes of
    the contained :obj:`stream`, except for the following:

     * :meth:`read*` and :meth:`write*`. These methods are not
       supported, because byte-oriented read and write operations
       would invalidate the internal state maintained by :class:`SlipStream`.
     * Similarly, :meth:`seek`, :meth:`tell`, and :meth:`truncate` are not supported,
       because repositioning or truncating the stream would invalidate the internal state.
     * :meth:`raw`, :meth:`detach` and other methods that provide access to or manipulate
       the stream's internal data.

    In stead of the :meth:`read*` and :meth:`write*` methods
    a :class:`SlipStream` object provides the method :meth:`recv_msg` and :meth:`send_msg`
    to read and write SLIP-encoded messages.

    .. deprecated:: 0.6
       Direct access to the methods and attributes of the contained :obj:`stream`
       will be removed in version 1.0

    """

    def __init__(self, stream: _ProtoStream, chunk_size: int = io.DEFAULT_BUFFER_SIZE):
        # pylint: disable=missing-raises-doc
        """
        To instantiate a :class:`SlipStream` object, the user must provide
        a pre-constructed open byte stream that is ready for reading and/or writing

        Args:
            stream (bytestream): The byte stream that will be wrapped.

            chunk_size: the number of bytes to read per read operation.
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
                raise TypeError(
                    f"{stream.__class__.__name__} object has no method {method}"
                )
        if hasattr(stream, "encoding"):
            raise TypeError(f"{stream.__class__.__name__} object is not a byte stream")
        self._chunk_size = chunk_size if chunk_size > 0 else io.DEFAULT_BUFFER_SIZE
        super().__init__(stream)

    def send_bytes(self, packet: bytes) -> None:
        """See base class"""
        while packet:
            number_of_bytes_written = self.stream.write(packet)
            packet = packet[number_of_bytes_written:]

    def recv_bytes(self) -> bytes:
        """See base class"""
        return b"" if self._stream_is_closed else self.stream.read(self._chunk_size)

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
        if (
            attribute.startswith("read")
            or attribute.startswith("write")
            or attribute
            in (
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
            )
        ):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{attribute}'"
            )
        warnings.warn(
            "Direct access to the enclosed stream attributes and methods will be removed in version 1.0",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self.stream, attribute)
