# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import socket
from .slipwrapper import SlipWrapper


class SlipSocket(SlipWrapper):
    """SlipSocket -> Wraps a TCP :class:`socket` with a :class:`Driver`

    :class:`SlipSocket` combines a :class:`Driver` instance with a
    :class:`socket`.
    The :class:`SlipStream` class has all the methods from its base class :class:`SlipWrapper`.
    In addition it directly exposes all methods and attributes of
    the contained :obj:`socket`, except for the following:

    * :meth:`send*` and :meth:`recv*`. These methods are not
      supported, because byte-oriented send and receive operations
      would invalidate the internal state maintained by :class:`SlipSocket`.
    * Similarly, :meth:`makefile` is not supported, because byte- or line-oriented
      read and write operations would invalidate the internal state.
    * :meth:`share` (Windows only) and :meth:`dup`. The internal state of
      the :class:`SlipSocket` would have to be duplicated and shared to make these methods meaningful.
      Because of the lack of a convincing use case for this, sharing and duplication is
      not supported.
    * The :meth:`accept` method is delegated to the contained :class:`socket`,
      but the socket that is returned by the :class:`socket`'s :meth:`accept` method
      is automatically wrapped in a :class:`SlipSocket` object.

    In stead of the :class:`socket`'s :meth:`send*` and :meth:`recv*` methods
    a :class:`SlipSocket` provides the method :meth:`send_msg` and :meth:`recv_msg`
    to send and receive SLIP-encoded messages.

    Only TCP sockets are supported. Using the SLIP protocol on
    UDP sockets is not supported for the following reasons:

    * UDP is datagram-based. Using SLIP with UDP therefore
      introduces ambiguity: should SLIP packets be allowed to span
      multiple UDP datagrams or not?
    * UDP does not guarantee delivery, and does not guarantee that
      datagrams are delivered in the correct order.

    """
    _chunk_size = 4096

    def __init__(self, sock):
        """
        To instantiate a :class:`SlipSocket`, the user must provide
        a pre-constructed TCP :class:`socket`.
        An alternative way to instantiate s SlipSocket is to use the
        class method :meth:`create_connection`.

        :param socket.socket sock: an existing TCP socket, i.e.
           a socket with type :const:`socket.SOCK_STREAM`
        """

        if not isinstance(sock, socket.socket) or sock.type != socket.SOCK_STREAM:
            raise ValueError('Only sockets with type SOCK_STREAM are supported')
        super().__init__(sock)
        self.socket = self.stream

    def send_bytes(self, packet):
        self.socket.sendall(packet)

    def recv_bytes(self):
        return self.socket.recv(self._chunk_size)

    def accept(self):
        conn, address = self.socket.accept()
        return self.__class__(conn), address

    @property
    def family(self):
        return self.socket.family

    @property
    def type(self):
        return self.socket.type

    @property
    def proto(self):
        return self.socket.proto

    def __getattr__(self, attribute):
        if attribute.startswith('recv') or attribute.startswith('send') or attribute in (
            'makefile', 'share', 'dup',
        ):
            raise AttributeError("'{}' object has no attribute '{}'".
                                 format(self.__class__.__name__, attribute))
        return getattr(self.socket, attribute)

    @classmethod
    def create_connection(cls, address, timeout=None, source_address=None):
        """Create a SlipSocket connection.

        This convenience method creates a connection to the the specified address
        using the :func:`socket.create_connection` function.
        The socket that is returned from that call is automatically wrapped in
        a :class:`SlipSocket` object.

        .. note::
            The :meth:`create_connection` method does not magically turn the
            socket at the remote address into a SlipSocket.
            For the connection to work properly,
            the remote socket must already
            have been configured to use the SLIP protocol.
        """
        sock = socket.create_connection(address, timeout, source_address)
        return cls(sock)
