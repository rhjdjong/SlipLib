:py:mod:`slip` --- A module for the SLIP protocol
=================================================

.. module:: slip
   :synopsis: Module that provides support for the SLIP protocol.
.. moduleauthor:: Ruud de Jong <rhjdjong@gmail.com>
.. Copyright (C) 2015 Ruud de Jong


The :py:mod:`slip` module implements the encoding and decoding functionality
for SLIP packets, as described in :rfc:`1055`.

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

=============== ========= =================================================
Byte value      Name      Purpose
=============== ========= =================================================
:code:`b'\xc0'` *END*     to delimit messages
:code:`b'\xdb'` *ESC*     to escape *END* or *ESC* bytes in the message
:code:`b'\xdc'` *ESC_END* the escaped value of the *END* byte
:code:`b'\xdd'` *ESC_ESC* the escaped value of the *ESC* byte
=============== ========= =================================================

An *END* byte in the message is encoded as the sequence
*ESC+ESC_END* (:code:`b'\xdb\xdc'`)
in the slip packet,
and an *ESC* byte  in the message is encoded
as the sequence *ESC+ESC_ESC* (:code:`b'\xdb\xdd'`).

======================== =====================================
Original                 Encoded
======================== =====================================
:code:`b'\xc0'` (*END*)  :code:`b'\xdb\xdc'` (*ESC+ESC_END*)
:code:`b'\xdb'` (*ESC*)  :code:`b'\xdb\xdd'` (*ESC+ESC_ESC*)
======================== =====================================

As a consequence, an *ESC* byte in a slip packet
must always be followed by an *ESC_END* or an *ESC_ESC* byte;
anything else is a protocol error.
Although the implementation code proposed by :rfc:`1055`
ignores such errors, the :py:mod:`slip` module raises a
:py:exc:`SlipDecodingError`
exception in such cases.
