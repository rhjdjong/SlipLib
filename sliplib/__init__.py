"""The :mod:`sliplib` module provides a :class:`Driver` class
for encoding and decoding of messages according to
the SLIP protocol, as defined in :rfc:`1055`.

"""

__version__ = '0.1.0'

__all__ = ['encode',
           'decode',
           'is_valid',
           'Driver',
           'ProtocolError',
           '__version__']

from .slip import (encode, decode, is_valid, Driver, ProtocolError)
