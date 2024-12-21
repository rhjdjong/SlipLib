#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
Module :mod:`~sliplib.slipsocket`
=================================

The :mod:`~sliplib.slipsocket` module contains the class :class:`SlipSocket`.
The :class:`SlipSocket` class can also be imported directly from the :mod:`sliplib` package.

.. autoclass:: TCPAddress

.. autoclass:: SlipSocket(sock)
   :show-inheritance:

   Class :class:`SlipSocket` offers the following methods in addition to the methods
   offered by its base class :class:`~sliplib.slipwrapper.SlipWrapper`:

   .. automethod:: accept
   .. automethod:: create_connection

   .. note::
       The :meth:`accept` and :meth:`create_connection` methods
       do not magically turn the
       socket at the remote address into a socket that uses the SLIP protocol.
       For the connection to work properly,
       the remote socket must already
       have been configured to use the SLIP protocol.

   The following commonly used :class:`socket.socket` methods are exposed through
   a :class:`SlipSocket` object.
   These methods are simply delegated to the wrapped :class:`socket.socket` instance.
   See the documentation for :class:`socket.socket` for more information on these methods.

   .. automethod:: bind
   .. automethod:: close
   .. automethod:: connect
   .. automethod:: connect_ex
   .. automethod:: fileno
   .. automethod:: getpeername
   .. automethod:: getsockname
   .. method:: getsockopt(level, optname, ...)

      Get the socket option from the embedded socket.
      See the documentation for :meth:`socket.socket.getsockopt` for more information about the parameters.

      :param level: The socket option level.
      :type level: int
      :param optname: The socket option name.
      :type optname: int
      :param ...: Other valid argument(s) depending on the option.

      :rtype: :external:obj:`~typing.Union` [:obj:`int`, :obj:`bytes`]
      :return: The integer or bytes representing the value of the socket option.

   .. automethod:: gettimeout
   .. automethod:: listen([backlog])
   .. method:: setsockopt(level, optname, ...)

      Set the socket option of the embedded socket.
      See the documentation for :meth:`socket.socket.setsockopt` for more information about the parameters.

      :param level: The socket option level.
      :type level: int
      :param optname: The socket option name.
      :type optname: int
      :param ...: Other valid argument(s) depending on the option.
      :rtype: :external:obj:`None`

   .. automethod:: shutdown

   Since the wrapped socket is available as the :attr:`socket` attribute,
   any other :class:`socket.socket`
   method can be invoked through that attribute.

   .. warning::

      Avoid using :class:`socket.socket`
      methods that affect the bytes that are sent or received through the socket.
      Doing so will invalidate the internal state of the enclosed :class:`~sliplib.slip.Driver` instance,
      resulting in corrupted SLIP messages.
      In particular, do not use any of the :meth:`recv*` or :meth:`send*` methods
      on the :attr:`socket` attribute.

   A :class:`SlipSocket` instance has the following attributes
   and read-only properties in addition to the attributes and properties
   offered by its base class :class:`~sliplib.slipwrapper.SlipWrapper`:

   .. autoattribute:: socket
   .. autoproperty:: family
   .. autoproperty:: type
   .. autoproperty:: proto
"""

from __future__ import annotations

import socket
import warnings
from typing import Any, Tuple, Union, cast

from sliplib import use_leading_end_byte
from sliplib.slipwrapper import SlipWrapper

#: TCPAddress stands for either an IPv4 address, a :obj:`(host: str, port: int)` tuple,
#: or an IPv6 address, a :obj:`(host: str, port: int, flowinfo: int, scope_id: int)` tuple.
TCPAddress = Union[Tuple[str, int], Tuple[str, int, int, int]]


class SlipSocket(SlipWrapper[socket.socket]):
    """Class that wraps a TCP :external:obj:`~socket.socket` with a :class:`~sliplib.slip.Driver`.

    :class:`SlipSocket` combines a :class:`~sliplib.slip.Driver` instance with a
    :external:obj:`~socket.socket`.
    The :class:`SlipSocket` class has all the methods from its base class :class:`~sliplib.slipwrapper.SlipWrapper`.
    In addition, it directly exposes all methods and attributes of
    the contained :external:obj:`~socket.socket`, except for the following:

    * :meth:`send*` and :meth:`recv*`. These methods are not
      supported, because byte-oriented send and receive operations
      would invalidate the internal state maintained by :class:`SlipSocket`.
    * Similarly, :meth:`makefile` is not supported, because byte- or line-oriented
      read and write operations would invalidate the internal state.
    * :meth:`share` (Windows only) and :meth:`dup`. The internal state of
      the :class:`SlipSocket` would have to be duplicated and shared to make these methods meaningful.
      Because of the lack of a convincing use case for this, sharing and duplication is
      not supported.
    * The :meth:`accept` method is delegated to the contained :external:obj:`socket.socket`.
      The socket that is returned by the socket's :external:obj:`accept() <socket.socket.accept>` method
      is automatically wrapped in a :class:`SlipSocket` object.

    Instead of the :external:obj:`~socket.socket`'s :meth:`send*` and :meth:`recv*` methods
    a :class:`SlipSocket` provides the method :meth:`~sliplib.slipwrapper.SlipWrapper.send_msg`
    and :meth:`~sliplib.slipwrapper.SlipWrapper.recv_msg`
    to send and receive SLIP-encoded messages.

    .. deprecated:: 0.6
       Direct access to the methods and attributes of the contained :external:obj:`socket.socket`
       other than :attr:`family`, :attr:`type`, and :attr:`proto` will be removed in version 1.0

    Only TCP sockets are supported. Using the SLIP protocol on
    UDP sockets is not supported for the following reasons:

    * UDP is datagram-based. Using SLIP with UDP therefore
      introduces ambiguity: should SLIP packets be allowed to span
      multiple UDP datagrams or not?
    * UDP does not guarantee delivery, and does not guarantee that
      datagrams are delivered in the correct order.

    """

    _chunk_size = 4096

    def __init__(self, sock: socket.SocketType):
        """
        To instantiate a :class:`SlipSocket`, the user must provide
        a pre-constructed TCP :external:obj:`~socket.socket`.
        An alternative way to instantiate s SlipSocket is to use the
        class method :meth:`create_connection`.

        Args:
            sock (socket.socket): An existing TCP socket, i.e.
                a socket with type :external:obj:`socket.SOCK_STREAM`
        """

        if not isinstance(sock, socket.socket) or sock.type != socket.SOCK_STREAM:
            error_msg = "Only sockets with type SOCK_STREAM are supported."
            raise ValueError(error_msg)
        super().__init__(sock)

        #: The wrapped :class:`~socket.socket`.
        #: This is actually just an alias for the :attr:`~sliplib.slipwrapper.SlipWrapper.stream`
        #: attribute in the base class.
        self.socket = self.stream

    def send_bytes(self, packet: bytes) -> None:
        """See base class"""
        self.socket.sendall(packet)

    def recv_bytes(self) -> bytes:
        """See base class"""
        return self.socket.recv(self._chunk_size)

    def accept(self) -> tuple[SlipSocket, TCPAddress]:
        """Accept an incoming connection.

        Returns a :class:`SlipSocket` and a remote :class:`TCPAddress`.
        The returned :class:`SlipSocket` inherits the leading-end-byte behavior of the
        :class:`SlipSocket` instance on which :meth:`accept` was called.

        :rtype: (:class:`SlipSocket`, :class:`TCPAddress`):
        :returns: A tuple with a :class:`SlipSocket` object and the remote IP address.
        """
        conn, address = self.socket.accept()
        with use_leading_end_byte(self.driver.sends_leading_end_byte):
            accept_socket = self.__class__(conn)
        return accept_socket, address

    def bind(self, address: TCPAddress) -> None:
        """Bind the :class:`SlipSocket` instance to `address`.

        Args:
            address (:class:`TCPAddress`):  The address to bind to.
        """
        self.socket.bind(address)

    def close(self) -> None:
        """Close the :class:`SlipSocket` instance."""
        self.socket.close()

    def connect(self, address: TCPAddress) -> None:
        """Connect the :class:`SlipSocket` instance to a remote socket at `address`.

        Args:
            address (:class:`TCPAddress`): The IP address of the remote socket.
        """
        self.socket.connect(address)

    def connect_ex(self, address: TCPAddress) -> None:
        """Connect the :class:`SlipSocket` instance to a remote socket at `address`.

        Args:
            address (:class:`TCPAddress`): The IP address of the remote socket.
        """
        self.socket.connect_ex(address)

    def fileno(self) -> int:
        """Get the socket's file descriptor.

        Returns:
            The wrapped socket's file descriptor, or -1 on failure.
        """
        return self.socket.fileno()

    def getpeername(self) -> TCPAddress:
        """Get the IP address of the remote socket to which the :class:`SlipSocket` instance is connected.

        :rtype: :class:`TCPAddress`
        Returns:
            The remote IP address.
        """
        return cast(TCPAddress, self.socket.getpeername())

    def getsockname(self) -> TCPAddress:
        """Get the :class:`SlipSocket` instance's own address.

        :rtype: :class:`TCPAddress`
        Returns:
            The local IP address.
        """
        return cast(TCPAddress, self.socket.getsockname())

    def getsockopt(self, *args: Any) -> int | bytes:
        """Get the socket option from the embedded socket.

        Args:
            level: The socket option level.
            optname: The socket option name.
            buflen: The maximum buffer length to use.

        Returns:
            The integer or bytes representing the value of the socket option.
        """
        return self.socket.getsockopt(*args)

    def gettimeout(self) -> float | None:
        """Get the timeout in seconds.

        Returns:
            The timeout value, or :external:obj:`None` if no timeout is set.
        """
        return self.socket.gettimeout()

    def listen(self, backlog: int | None = None) -> None:
        """Enable a :class:`SlipSocket` server to accept connections.

        Args:
            backlog (int): The maximum number of waiting connections.
        """
        if backlog is None:
            self.socket.listen()
        else:
            self.socket.listen(backlog)

    def setsockopt(self, *args: Any) -> None:
        """Get the socket option from the embedded socket.

        Returns:
            The integer or bytes representing the value of the socket option.
        """
        return self.socket.setsockopt(*args)

    def shutdown(self, how: int) -> None:
        """Shutdown the connection.

        Args:
            how: Flag to indicate which halves of the connection must be shut down.
        """
        self.socket.shutdown(how)

    @property
    def family(self) -> int:
        """The wrapped socket's address family.

        Usually :external:obj:`socket.AF_INET` (IPv4) or :external:obj:`socket.AF_INET6` (IPv6).
        """
        return self.socket.family

    @property
    def type(self) -> int:
        """The wrapped socket's type.

        Always :external:obj:`socket.SOCK_STREAM`.
        """
        return self.socket.type

    @property
    def proto(self) -> int:
        """The wrapped socket's protocol number.

        Usually 0.
        """
        return self.socket.proto

    def __getattr__(self, attribute: str) -> Any:
        if attribute.startswith(("recv", "send")) or attribute in (
            "makefile",
            "share",
            "dup",
        ):
            error_msg = f"'{self.__class__.__name__}' object has no attribute '{attribute}'"
            raise AttributeError(error_msg)
        warnings.warn(
            "Direct access to the enclosed socket attributes and methods will be removed in version 1.0",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self.socket, attribute)

    @classmethod
    def create_connection(
        cls,
        address: TCPAddress,
        timeout: float | None = None,
        source_address: TCPAddress | None = None,
    ) -> SlipSocket:
        """Create a :class:`SlipSocket` connection.

        This convenience method creates a connection to a socket at the specified address
        using the :func:`socket.create_connection` function.
        The socket that is returned from that call is wrapped in
        a :class:`SlipSocket` object.

        Args:
            address (:class:`TCPAddress`): The remote address.
            timeout: Optional timeout value.
            source_address (:obj:`Optional` [:class:`TCPAddress`]): Optional local address for the near socket.

        Returns:
            A :class:`SlipSocket` instance that is connected to the socket at the remote address.

        See Also:
            :func:`socket.create_connection`
        """
        # noinspection PyTypeChecker
        sock = socket.create_connection(address[0:2], timeout, source_address)
        return cls(sock)
