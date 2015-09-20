``sliplib`` --- A module for the SLIP protocol
==============================================

.. image:: https://readthedocs.org/projects/sliplib/badge/?version=latest
   :target: http://sliplib.readthedocs.org/en/latest/?badge=latest
   :alt: Documentation Status
   
The ``sliplib`` module implements the encoding and decoding
functionality for SLIP packets, as described in :rfc:`1055`.
It defines encoding and decoding functions and classes,
and registers these in the
`codecs <https://docs.python.org/3/library/codecs.html#module-codecs>`_ module.

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
   :header: "Original", "Encoded"

   ``b'\xc0'``, ``b'\xdb\xdc'``
   ``b'\xdb'``, ``b'\xdb\xdd'``


As a consequence, an *ESC* byte in a slip packet
must always be followed by an *ESC_END* or an *ESC_ESC* byte;
anything else is a protocol error.
Although the implementation code proposed by :rfc:`1055`
ignores such errors, the ``sliplib`` module raises an
exception in such cases.

