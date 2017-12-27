
.. image:: https://readthedocs.org/projects/sliplib/badge/?version=latest
   :target: http://sliplib.readthedocs.org/en/latest/?badge=latest
   :alt: ReadTheDocs Documentation Status

.. image:: https://travis-ci.org/rhjdjong/SlipLib.svg
   :target: https://travis-ci.org/rhjdjong/SlipLib
   :alt: Travis Test Status

.. image:: https://ci.appveyor.com/api/projects/status/rqe1ufitabs5niy9?svg=true
   :target: https://ci.appveyor.com/project/RuuddeJong/sliplib
   :alt: AppVeyor Test Status



==============================================
``sliplib`` --- A module for the SLIP protocol
==============================================


The `sliplib` module implements the encoding and decoding
functionality for SLIP packets, as described in :rfc:`1055`.
It defines encoding, decoding, and validation functions,
as well as a  driver class that can be used to implement
a SLIP protocol stack, and higher-level classes that
apply the SLIP protocol to TCP connections or IO streams.
Read the `documentation <http://sliplib.readthedocs.org/en/latest/>`
for detailed information.

Background
==========

The SLIP protocol is described in :rfc:`1055` (:title:`A Nonstandard for
Transmission of IP Datagrams over Serial Lines: SLIP`, J. Romkey,
June 1988).  The original purpose of the protocol is
to provide a mechanism to indicate the boundaries of IP packets,
in particular when the IP packets are sent over a connection that
does not provide a framing mechanism, such as serial lines or
dial-up connections.

There is, however, nothing specific to IP in the SLIP protocol.
SLIP offers a generic framing method that can be used for any
type of data that must be transmitted over a (continuous) byte stream.
In fact, the main reason for creating this module
was the need to communicate with a third-party application that
used SLIP over TCP (which is a continuous byte stream)
to frame variable length data structures.


Usage
=====

Low-level usage
---------------

The recommended basic usage is to run all encoding and decoding operations
through an instantiation `driver` of the `Driver` class, in combination
with the appropriate I/O code.
The `Driver` class itself works without any I/O, and can therefore be used with
any networking code, or any bytestream like pipes, serial I/O, etc.
It can work in synchronous as well as in asynchronous environments.

The `Driver` class offers the methods
`send` and `receive` to handle
the conversion between messages and SLIP-encoded packets.

High-level usage
----------------

The module also provides a `SlipWrapper` abstract baseclass
that provides the methods `send_msg` and `recv_msg` to send
and receive single SLIP-encoded messages. This base class
wraps an instance of the `Driver` class with a user-provided stream.

Two concrete subclasses of `SlipWrapper` are provided:

* `SlipStream` allows the wrapping of a buffered IO stream.
* `SlipSocket` allows the wrapping of a TCP socket.

In addition, the module also provides a `SlipRequestHandler`
to facilitate the creation of TCP servers that can handle
SLIP-encoded messages.


Error Handling
==============

Contrary to the reference implementation described in :rfc:`1055`,
which chooses to essentially ignore protocol errors,
the functions and classes in the `sliplib` module
uses a `ProtocolError` exception
to indicate protocol errors, i.e. SLIP packets with invalid byte sequences.
The `Driver` class raises the `ProtocolError` exception
as soon as a SLIP packet with an invalid byte sequence is received .
The `SlipWrapper` class and its subclasses catch the `ProtocolError`\s
raised by the `Driver` class, and re-raise them when
an attempt is made to read the contents of a SLIP packet with invalid data.

