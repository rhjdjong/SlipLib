"""The :mod:`slip` module provides functions and classes
that allow encoding and decoding of messages according to
the SLIP protocol, as defined in :rfc:`1055`.

The module defines encoding and decoding functions,
an incremental encoder and decoder, and stream wrappers
for the slip protocol.
It also registers these with the :mod:`codecs` package.
"""

__version__ = '0.0.1'

__all__ = ['encode', 'decode', 'SlipDecodingError',
           'END', 'ESC', 'ESC_END', 'ESC_ESC', '__version__']

from .slip import (encode, decode, SlipDecodingError,
                   SlipIncrementalDecoder, SlipIncrementalEncoder,
                   SlipStreamReader, SlipStreamWriter,
                   END, ESC, ESC_END, ESC_ESC)