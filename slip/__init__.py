__version__ = '0.0.1'

__all__ = ['encode', 'decode', 'SlipDecodingError',
           'END', 'ESC', 'ESC_END', 'ESC_ESC', 'ENDb', 'ESCb', '__version__']

from .slip import (encode, decode, SlipDecodingError,
                   END, ESC, ESC_END, ESC_ESC)