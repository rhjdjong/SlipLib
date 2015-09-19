'''
Created on 29 jun. 2015

@author: Ruud de Jong
'''

import codecs
import io
import re
try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable
from functools import partial

class SlipDecodingError(ValueError):
    '''Indicates that a byte sequence cannot be decoded.'''


END = 0xc0
ESC = 0xdb
ESC_END = 0xdc
ESC_ESC = 0xdd
"""These constants represent the values for the special SLIP bytes."""

_ENDb = bytes((END,))
_ESCb = bytes((ESC,))
_E_ENDb = bytes((ESC_END,))
_E_ESCb = bytes((ESC_ESC,))
_ESC_ENDb = bytes((ESC, ESC_END))
_ESC_ESCb = bytes((ESC, ESC_ESC))

_invalid_esc_sequence_re = re.compile(_ESCb + b'(?:([^'+_E_ENDb+_E_ESCb
                                      +br'])|(\Z))')

class SlipEncoder():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encoded_bytes = bytearray()

    def encode(self, obj, errors=None, final=False):
        if not isinstance(obj, Iterable):
            obj = (obj,)
        self.encoded_bytes.extend(bytes(obj))
        
        if final:
            packet = bytearray()
            if self.encoded_bytes:
                packet.append(END)
                packet.extend(self.encoded_bytes.replace(_ESCb, _ESC_ESCb).
                                                 replace(_ENDb, _ESC_ENDb))
                packet.append(END)
            self.reset()
            return packet

    def reset(self):
        del self.encoded_bytes[:]
    
    def getstate(self):
        return 0
    
    def setstate(self, state):
        pass
        

class SlipDecoder():        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_buffer = b''

    def decode(self, obj, errors=None, final=False):
        if not isinstance(obj, Iterable):
            obj = (obj,)
        self.input_buffer += bytes(obj)
        self.input_buffer = self.input_buffer.lstrip(_ENDb)
        
        packet = b''
        if END in self.input_buffer:
            packet, rest = self.input_buffer.split(_ENDb, 1)
            self.input_buffer = rest.lstrip(_ENDb)
        elif final:
            packet = self.input_buffer
            self.input_buffer = b''
        
        if packet or final:
            # Verify that ESC is always followed by ESC_END or ESC_ESC
            # If not, something has gone wrong in the encoding process
            match = _invalid_esc_sequence_re.search(packet)
            if match:
                b = match.group(1)
                if b:
                    msg = 'Invalid escape sequence ESC-{}'.format(b)
                else:
                    msg = 'Unfinished escape sequence'
                raise SlipDecodingError(msg)                  

            if final and self.input_buffer:
                msg = 'Remaining undecoded bytes: {!r}'.format(self.input_buffer)
                self.reset()
                raise SlipDecodingError(msg)
                
            return packet.replace(_ESC_ENDb, _ENDb).replace(_ESC_ESCb, _ESCb)
        
    def reset(self):
        self.input_buffer = b''
    
    def getstate(self):
        return 0
    
    def setstate(self, state):
        pass
        
        
encode = partial(SlipEncoder().encode, errors=None, final=True)
decode = partial(SlipDecoder().decode, errors=None, final=True)

encode.__doc__ = '''Encode a message in a SLIP packet.

The function returns a SLIP packet with the encoded message.
The SLIP packet contains exactly one
leading and trailing :data:`END` byte.

Args:
    obj (byte or byte iterable): the message to be encoded.

Returns:
    bytes: the SLIP-encoded message.
'''
decode.__doc__ = '''Decode a SLIP packet.

The function must be called with exactly one SLIP packet.
This means that, apart from leading and trailing :data:`END` bytes,
*obj* must contain no other :data:`END` bytes.

Args:
    obj (byte iterable): the SLIP packet to be decoded.

Returns:
    bytes: the message contained in the packet.
    
Raises:
    SlipDecodingError: when *obj* cannot be decoded.
'''


class SlipIncrementalEncoder(SlipEncoder, codecs.IncrementalEncoder):
    pass


class SlipIncrementalDecoder(SlipDecoder, codecs.IncrementalDecoder):
    pass


class SlipStreamWriter(SlipEncoder, codecs.StreamWriter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def write(self, msg):
        packet = self.encode(msg, final=True, errors=self.errors)
        self.stream.write(packet)
    
    def writelines(self, msg_list):
        for msg in msg_list:
            self.write(msg)
            

class SlipStreamReader(SlipDecoder, codecs.StreamReader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read(self, size=None, chars=None, firstline=None):
        final = False
        msg = self.decode(b'', final=final)
        while msg is None:
            buffer = self.stream.read(io.DEFAULT_BUFFER_SIZE)
            if len(buffer) == 0:
                final=True
            msg = self.decode(buffer, final=final)
        return msg
    
    def readline(self, keepends=False):
        return self.read()
    
    def readlines(self, n, keepends=False):
        return [self.read() for _ in range(n)]
        
    
def _search_slip_codec(encoding):
    if encoding == 'slip':
        return codecs.CodecInfo(
                name='Slip',
                encode=encode,
                decode=decode,
                incrementalencoder=SlipIncrementalEncoder,
                incrementaldecoder=SlipIncrementalDecoder,
                streamreader=SlipStreamReader,
                streamwriter=SlipStreamWriter,
        )
    return None

codecs.register(_search_slip_codec)

