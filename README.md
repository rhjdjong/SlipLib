[![Stable Version](https://img.shields.io/pypi/v/sliplib?color=blue)](https://pypi.org/project/sliplib/)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
![tests](https://github.com/rhjdjong/SlipLib/actions/workflows/test.yml/badge.svg)
[![Coverage](https://coveralls.io/repos/github/rhjdjong/SlipLib/badge.svg?branch=main)](https://coveralls.io/github/rhjdjong/SlipLib?branch=main)
[![Documentation Status](https://readthedocs.org/projects/sliplib/badge/?version=main)](https://sliplib.readthedocs.io/en/main/?badge=main)

# `sliplib` &mdash; A module for the SLIP protocol

The `sliplib` module implements the encoding and decoding
functionality for SLIP packets, as described in
[RFC 1055][rfc1055].
It defines encoding, decoding, and validation functions,
as well as a driver class that can be used to implement
a SLIP protocol stack, and higher-level classes that
apply the SLIP protocol to TCP connections or IO streams.
Read the [documentation](http://sliplib.readthedocs.org/en/main/)
for detailed information.

## Background

The SLIP protocol is described in [RFC 1055][rfc1055] (*A Nonstandard for
Transmission of IP Datagrams over Serial Lines: SLIP*, J. Romkey,
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


## Usage

### Installation

To install the `sliplib` module, use

```
pip install sliplib
```

### Low-level usage

The recommended basic usage is to run all encoding and decoding operations
through an instantiation `driver` of the `Driver` class, in combination
with the appropriate I/O code.
The `Driver` class itself works without any I/O, and can therefore be used with
any networking code, or any bytestream like pipes, serial I/O, etc.
It can work in synchronous as well as in asynchronous environments.

### High-level usage

The `sliplib` package  also provides a `SlipWrapper` abstract baseclass
that provides the methods `send_msg` and `recv_msg` to send
and receive single SLIP-encoded messages. This base class
wraps an instance of the `Driver` class with a user-provided stream.

Two concrete subclasses of `SlipWrapper` are provided:

* `SlipStream` allows the wrapping of a byte IO stream.
* `SlipSocket` allows the wrapping of a TCP socket.

In addition, the module also provides a `SlipRequestHandler`
to facilitate the creation of TCP servers that can handle
SLIP-encoded messages.


## Error Handling

Contrary to the reference implementation described in [RFC 1055][rfc1055],
which chooses to essentially ignore protocol errors,
the functions and classes in the `sliplib` module
raise a `ProtocolError` exception
when handling a SLIP packet with invalid contents.

[rfc1055]: http://tools.ietf.org/html/rfc1055.html
