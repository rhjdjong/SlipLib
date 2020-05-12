#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

import io

from .slipwrapper import SlipWrapper


class SlipStream(SlipWrapper):
    """Class that wraps an IO stream with a :class:`Driver`

    :class:`SlipStream` combines a :class:`Driver` instance with an
    :class:`IOBase` byte stream.

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
    """
    def __init__(self, stream, chunk_size=io.DEFAULT_BUFFER_SIZE):
        """
        To instantiate a :class:`SlipStream` object, the user must provide
        a pre-constructed open byte stream that is ready for reading and/or writing

        :param stream: an existing byte stream.
        :param chunk_size: the number of bytes to read from the stream in one read operation.
            Default value is `io.DEFAULT_BUFFER_SIZE`.

        .. versionadded:: 0.6
           The `chunk_size` parameter.

        A :class:`SlipStream` instance can e.g. be usefui to read slip-encoded messages
        from a file:

        .. code::

            with open('/path/to/a/slip/encoded/file', mode='rb') as f:
                slip_file = SlipStream(f)
                for msg in slip_file:
                    # Do something with the message

        """
        for method in ('read', 'write'):
            if not hasattr(stream, method) or not callable(getattr(stream, method)):
                raise TypeError('{} object has no method {}'.format(stream.__class__.__name__, method))
        if hasattr(stream, 'encoding'):
            raise TypeError('{} object is not a byte stream'.format(stream.__class__.__name__))
        self._chunk_size = chunk_size if chunk_size > 0 else io.DEFAULT_BUFFER_SIZE
        self._stream_closed = False
        super().__init__(stream)

    def send_bytes(self, packet):
        while len(packet) > 0:
            number_of_bytes_written = self.stream.write(packet)
            packet = packet[number_of_bytes_written:]

    def recv_bytes(self):
        return b'' if self._stream_is_closed else self.stream.read(self._chunk_size)

    @property
    def _stream_is_closed(self):
        return getattr(self.stream, 'closed', False)

    def __getattr__(self, attribute):
        if attribute in ('readable', 'writable'):
            return getattr(self.stream, attribute)
        if attribute.startswith('read') or attribute.startswith('write') or attribute in (
                'detach', 'flushInput', 'flushOutput', 'getbuffer', 'getvalue', 'peek', 'raw', 'reset_input_buffer',
                'reset_output_buffer', 'seek', 'seekable', 'tell', 'truncate'
        ):
            raise AttributeError("'{}' object has no attribute '{}'".
                                 format(self.__class__.__name__, attribute))
        return getattr(self.stream, attribute)
