__version__ = '0.0.1'

__all__ = ['encode', 'decode', 'SlipDecodingError',
           'END', 'ESC', 'ESC_END', 'ESC_ESC', '__version__']

from .slip import (encode, decode, SlipDecodingError,
                   SlipIncrementalDecoder, SlipIncrementalEncoder,
                   SlipStreamReader, SlipStreamWriter,
                   END, ESC, ESC_END, ESC_ESC)