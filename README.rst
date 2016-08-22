
.. image:: https://readthedocs.org/projects/sliplib/badge/?version=latest
   :target: http://sliplib.readthedocs.org/en/latest/?badge=latest
   :alt: ReadTheDocs Documentation Status

.. image:: https://travis-ci.org/rhjdjong/SlipLib.svg
   :target: https://travis-ci.org/rhjdjong/SlipLib
   :alt: Travis Test Status

.. image:: https://ci.appveyor.com/api/projects/status/rqe1ufitabs5niy9?svg=true
   :target: https://ci.appveyor.com/project/RuuddeJong/sliplib
   :alt: AppVeyor Test Status
   
``sliplib`` --- A module for the SLIP protocol
==============================================

The ``sliplib`` module implements the encoding and decoding
functionality for SLIP packets, as described in :rfc:`1055`.
It defines encoding, decoding, and validation functions,
as well as a  driver class that can be used to implement
a SLIP protocol stack.


Background
----------

The SLIP protocol is described in :rfc:`1055` (:title:`A Nonstandard for
Transmission of IP Datagrams over Serial Lines: SLIP`, J. Romkey,
June 1988).  The original purpose of the protocol is
to provide a mechanism to indicate the boundaries of IP packets,
in particular when the IP packets are sent over a connection that
does not provide a framing mechanism, such as serial lines or
dial-up connections.

There is, however, nothing specific to IP in the SLIP protocol.
SLIP offers a generic framing method that can be used for any
type of message that must be transmitted over a (continuous) byte stream.
In fact, the main reason for creating this module
was the need to communicate with a third-party application that
used SLIP over TCP (which is a continuous byte stream)
to frame variable length messages.

The SLIP protocol uses four special byte values:

=============== ========= =============================================
Byte value      Name      Purpose
=============== ========= =============================================
:code:`0xc0`    *END*     to delimit messages
:code:`0xdb`    *ESC*     to escape *END* or *ESC* bytes in the message
:code:`0xdc`    *ESC_END* the escaped value of the *END* byte
:code:`0xdd`    *ESC_ESC* the escaped value of the *ESC* byte
=============== ========= =============================================

An *END* byte in the message is encoded as the sequence
*ESC+ESC_END* (:code:`b'\xdb\xdc'`)
in the slip packet,
and an *ESC* byte  in the message is encoded
as the sequence *ESC+ESC_ESC* (:code:`b'\xdb\xdd'`).

.. csv-table::
   :header: "Decoded", "Encoded"

   ``b'\xc0'``, ``b'\xdb\xdc'``
   ``b'\xdb'``, ``b'\xdb\xdd'``


As a consequence, an *ESC* byte in a slip packet
must always be followed by an *ESC_END* or an *ESC_ESC* byte;
anything else is a protocol error.

Usage
=====

The recommended usage is to run all encoding and decoding operations
through an instantiation ``driver`` of the ``Driver`` class, in combination
with the appropriate networking code.
The ``Driver`` class works without any IO, and can therefore be used with
any networking code.

To the application code that uses plain messages, the ``Driver`` class
offers the method ``send(msg)`` (to send a message)
and the read-only attribute ``messages`` (to obtain a list of received messages).
Similarly, to the networking code the ``Driver`` class offers the
method ``receive(data)`` (to process data received from the network) and
the read-only attribute ``packets`` (to obtain the encoded messages that are
available for sending out over the network).

The ``driver`` sits between the application code that uses plain messages,
and the networking code that works with SLIP-encoded packets.

Error Handling
==============

The reference implementation described in :rfc:`1055`
chooses to essentially ignore protocol errors,
i.e. invalid ESC sequences in a received packet.

Error handling in a ``Driver`` class instance depends on the value
of its attribute :code:`error`,
which can be set at creation time, and changed at any time thereafter.

When :code:`error` has the value :code:`'strict'`, protocol errors
result in a code:`ProtocolError` exception, and any offending packets
are not decoded.

Any other value of the :code:`error` attribute means that protocol errors
are ignored. Invalid or unfinshed escape sequences are copied as-is into
the message. This behaviour is *not* the same as the reference implementation
in :rfc:`1055`.

When the reference implementation encounters an invalid byte *b* following an *ESC* byte,
the *ESC* byte is ignored, and the byte *b* is copied into the decoded message.

The :module:`sliplib` non-strict error handling copies invalid *ESC X* byte
sequences as-is into the decoded message, with the exception of an *ESC END* byte
sequence. An *ESC END* byte sequence results in a finished decoded message with
a single *ESC* byte at the end.
