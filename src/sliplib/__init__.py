#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.


"""
Introduction
------------

The :mod:`sliplib` module implements the encoding and decoding
functionality for SLIP packets, as described in :rfc:`1055`.
It defines encoding, decoding, and validation functions,
as well as various classes that can be used to to wrap
the SLIP protocol over different kinds of byte streams.

The SLIP protocol uses four special byte values:

=============== ================ =============================================
Byte value      Name             Purpose
=============== ================ =============================================
:code:`0xc0`    :const:`END`     to delimit messages
:code:`0xdb`    :const:`ESC`     to escape :data:`END` or :data:`ESC` bytes in the message
:code:`0xdc`    :const:`ESC_END` the escaped value of the :data:`END` byte
:code:`0xdd`    :const:`ESC_ESC` the escaped value of the :data:`ESC` byte
=============== ================ =============================================

An :const:`END` byte in the message is encoded as the sequence
:const:`ESC+ESC_END` (:code:`b'\\\\xdb\\\\xdc'`)
in the slip packet,
and an :const:`ESC` byte  in the message is encoded
as the sequence :const:`ESC+ESC_ESC` (:code:`b'\\\\xdb\\\\xdd'`).

.. csv-table::
   :header: "Decoded", "Encoded"

   :code:`b'\\\\xc0'`, :code:`b'\\\\xdb\\\\xdc'`
   :code:`b'\\\\xdb'`, :code:`b'\\\\xdb\\\\xdd'`

As a consequence, an :const:`ESC` byte in an encoded SLIP packet
must always be followed by an :const:`ESC_END` or an :const:`ESC_ESC` byte;
anything else is a protocol error.

Low level Usage
---------------

.. automodule:: sliplib.slip

High Level Usage
----------------

.. automodule:: sliplib.slipwrapper
.. automodule:: sliplib.slipstream
.. automodule:: sliplib.slipsocket
.. automodule:: sliplib.slipserver

Exceptions
----------

.. currentmodule:: sliplib
.. autoexception:: ProtocolError
"""

from sliplib.slip import END, ESC, ESC_END, ESC_ESC, Driver, ProtocolError, decode, encode, is_valid
from sliplib.slipserver import SlipRequestHandler, SlipServer
from sliplib.slipsocket import SlipSocket
from sliplib.slipstream import SlipStream
from sliplib.slipwrapper import SlipWrapper

__all__ = [
    "encode",
    "decode",
    "is_valid",
    "Driver",
    "SlipWrapper",
    "SlipSocket",
    "SlipRequestHandler",
    "SlipServer",
    "SlipStream",
    "ProtocolError",
    "END",
    "ESC",
    "ESC_END",
    "ESC_ESC",
]
