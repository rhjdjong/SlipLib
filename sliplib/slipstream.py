# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import io
from .slipwrapper import SlipWrapper


class SlipStream(SlipWrapper):
    """Class that wraps an IO stream with a :class:`Driver`

    :class:`SlipStream` combines a :class:`Driver` instance with a
    :class:`BufferedIOBase` stream.

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
    a :class:`SlipSocket` provides the method :meth:`send_msg` and :meth:`recv_msg`
    to send and receive SLIP-encoded messages.
    """
    _chunk_size = io.DEFAULT_BUFFER_SIZE

    def __init__(self, stream):
        """
        To instantiate a :class:`SlipStream`, the user must provide
        a pre-constructed :class:`BufferedIOBase` stream.

        :param io.BufferedIOBase stream: an existing BufferedIOBase stream.
        """
        if not isinstance(stream, io.BufferedIOBase):
            raise ValueError('Only BufferedIOBase streams are supported')
        super().__init__(stream)

    def send_bytes(self, packet):
        self.stream.write(packet)

    def recv_bytes(self):
        return b'' if self.stream.closed else self.stream.read(self._chunk_size)

    def __getattr__(self, attribute):
        if attribute in (
                'detach', 'getbuffer', 'getvalue', 'peek', 'raw',
                'read', 'read1', 'readinto', 'readinto1', 'readline', 'readlines',
                'seek', 'tell', 'truncate', 'write', 'writelines'
        ):
            raise AttributeError("'{}' object has no attribute '{}'".
                                 format(self.__class__.__name__, attribute))
        return getattr(self.stream, attribute)
