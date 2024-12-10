#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.


"""
The SLIP Protocol
-----------------

The :mod:`sliplib` module implements the encoding and decoding
functionality for SLIP packets, as described in :rfc:`1055`.
It defines encoding, decoding, and validation functions,
as well as various classes that can be used to wrap
the SLIP protocol over different kinds of byte streams.

The SLIP protocol uses four special byte values, defined in the :attr:`~slip.config` configuration object.:

.. csv-table::
   :header:  "Name", "Byte value","Purpose"

   :const:`~slip.config.END`, :code:`b"\\\\xc0"`, To delimit messages.
   :const:`~slip.config.ESC`, :code:`b"\\\\xdb"`, "To escape :const:`~slip.config.END`
   or :const:`~slip.config.ESC` bytes in the message."
   :const:`~slip.config.ESC_END`, :code:`b"\\\\xdc"`, The escaped value of the :const:`~slip.config.END` byte.
   :const:`~slip.config.ESC_ESC`, :code:`b"\\\\xdd"`, The escaped value of the :const:`~slip.config.ESC` byte.

An :const:`~slip.config.END` byte in the message is encoded as the sequence
:const:`ESC+ESC_END` (:code:`b"\\\\xdb\\\\xdc"`)
in the slip packet,
and an :const:`~slip.config.ESC` byte  in the message is encoded
as the sequence :const:`ESC+ESC_ESC` (:code:`b"\\\\xdb\\\\xdd"`).

.. csv-table::
   :header: "Name", "Decoded", "Encoded"

   :const:`~slip.config.END`, :code:`b"\\\\xc0"`, :code:`b"\\\\xdb\\\\xdc"`
   :const:`~slip.config.ESC`, :code:`b"\\\\xdb"`, :code:`b"\\\\xdb\\\\xdd"`

As a consequence, an :const:`~slip.config.ESC` byte in an encoded SLIP packet
must always be followed by an :const:`~slip.config.ESC_END` or an :const:`~slip.config.ESC_ESC` byte;
anything else is a protocol error.

Protocol variations
-------------------

:rfc:`1055` specifies that the sender of a SLIP packet simply starts sending the encoded data,
followed by an :const:`~slip.config.END` byte after the last byte of the packet.

The RFC also mentions an alternative approach,
where an :const:`~slip.config.END` byte is sent both before the first byte
and after the last byte of the packet.
This is meant to minimize the possibility that line noise during the establishment of a connection
is interpreted as data in a SLIP packet.
This approach has the effect that the receiver will
see two back-to-back :const:`~slip.config.END` bytes between subsequent packets.
Therefore, this works only when the receiver treats those subsequent :const:`~slip.config.END` bytes
as a single :const:`~slip.config.END` byte.

In the :mod:`sliplib` package, SLIP packets are constructed by instances of the :class:`~slip.Driver` class.
Whether an :const:`~slip.config.END` byte is included as the first byte of a SLIP packet is a setting
in those instances, determined by the :attr:`config.USE_LEADING_END_BYTE <slip.config.USE_LEADING_END_BYTE>`
configuration value at the time the instances are created.

To accommodate receivers that do not work well with multiple :const:`~slip.config.END` bytes between SLIP packets,
the default value of :data:`config.USE_LEADING_END_BYTE <slip.config.USE_LEADING_END_BYTE>` is :external:obj:`False`.
However, some receivers may require received SLIP packets
to have both a leading and trailing :const:`~slip.config.END` byte.
For those cases the value of :data:`config.USE_LEADING_END_BYTE <slip.config.USE_LEADING_END_BYTE>`
can be set to :external:obj:`True`.

.. Note::
   The setting of :attr:`config.USE_LEADING_END_BYTE <slip.config.USE_LEADING_END_BYTE>` does not affect
   how :mod:`sliplib` handles *received* :const:`~slip.config.END` bytes. Independent of the setting,
   the :mod:`sliplib` code will always handle multiple subsequent :const:`~slip.config.END` bytes
   as a single :const:`~slip.config.END` byte.

.. important::

   The behavior of :class:`~slip.Driver` instances is determined
   by the value of :attr:`config.USE_LEADING_END_BYTE <slip.config.USE_LEADING_END_BYTE>`
   at the time the instance is created,
   either directly or through the instantiation of a :class:`~slipwrapper.SlipWrapper` subclass.
   Any change to :attr:`config.USE_LEADING_END_BYTE <slip.config.USE_LEADING_END_BYTE>`
   after the instance is created does not affect the behavior of that instance.
   The only exception to this rule is with the :meth:`SlipSocket.accept() <slipsocket.SlipSocket.accept>` method.
   When the :meth:`~slipsocket.SlipSocket.accept()` method is called
   on a :class:`~slipsocket.SlipSocket` instance :obj:`server`,
   it returns a new :class:`~slipsocket.SlipSocket` instance with the same behavior as :obj:`server`,
   regardless of the current value of :data:`config.USE_LEADING_END_BYTE <config.USE_LEADING_END_BYTE>`.

   If an application needs to always use leading :const:`~slip.config.END` bytes,
   it is recommended to import :mod:`slip.config`
   at the start of the application, and immediately set
   :data:`config.USE_LEADING_END_BYTE <slip.config.USE_LEADING_END_BYTE>`
   to :external:obj:`True` before creating any :mod:`sliplib` objects.

   If the application needs multiple connections, some of which require a leading :const:`~slip.config.END` byte
   and others that require the absence of a leading :const:`~slip.config.END` byte,
   the use of the :meth:`~config.use_leading_end_byte` context manager is recommended.

.. versionchanged:: 0.7.0
   Changed default behavior to *not* sending a leading :const:`~slip.config.END` byte.



"""

from sliplib.slip import (
    END,
    ESC,
    ESC_END,
    ESC_ESC,
    Driver,
    ProtocolError,
    config,
    decode,
    encode,
    is_valid,
    use_leading_end_byte,
)
from sliplib.slipserver import SlipRequestHandler, SlipServer
from sliplib.slipsocket import SlipSocket
from sliplib.slipstream import SlipStream
from sliplib.slipwrapper import SlipWrapper

__all__ = [
    "END",
    "ESC",
    "ESC_END",
    "ESC_ESC",
    "Driver",
    "ProtocolError",
    "SlipRequestHandler",
    "SlipServer",
    "SlipSocket",
    "SlipStream",
    "SlipWrapper",
    "config",
    "decode",
    "encode",
    "is_valid",
    "use_leading_end_byte",
]
