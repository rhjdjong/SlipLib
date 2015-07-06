'''
Created on 29 jun. 2015

@author: Ruud
'''

import codecs
import io
import collections.abc
from enum import IntEnum
from functools import partial

class SlipEncodingError(ValueError):
    pass

class SlipDecodingError(ValueError):
    pass


END = 0xc0       # SLIP message delimiter
ESC = 0xdb       # SLIP escape character
ESC_END = 0xdc   # Escaped SLIP END value
ESC_ESC = 0xdd   # Escaped SLIP ESC value

ENDb = bytes((END,))
ESCb = bytes((ESC,))
ESC_ENDb = bytes((ESC, ESC_END))
ESC_ESCb = bytes((ESC, ESC_ESC))

class SlipEncoder():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encoded_bytes = bytearray()

    def encode(self, obj, errors=None, final=False):
        if not isinstance(obj, collections.abc.Iterable):
            obj = (obj,)
        self.encoded_bytes.extend(bytes(obj))
        
        if final:
            packet = bytearray()
            if self.encoded_bytes:
                packet.append(END)
                packet.extend(self.encoded_bytes.replace(ESCb, ESC_ESCb).replace(ENDb, ESC_ENDb))
                packet.append(END)
            self.reset()
            return packet

    def reset(self):
        self.encoded_bytes.clear()
    
    def getstate(self):
        return 0
    
    def setstate(self, state):
        pass
        

class SlipDecoder():        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset(True)

    def decode(self, obj, errors=None, final=False):
        if errors is None:
            try:
                errors = self.errors
            except AttributeError:
                errors = 'strict'
        
        if not isinstance(obj, collections.abc.Iterable):
            obj = (obj,)
        self.input_buffer += bytes(obj)
        self.input_buffer = self.input_buffer.lstrip(ENDb)
        
        packet = b''
        if END in self.input_buffer:
            packet, rest = self.input_buffer.split(ENDb, 1)
            self.input_buffer = rest.lstrip(ENDb)
        elif final:
            packet = self.input_buffer
            self.input_buffer = b''
        
        if packet or final:
            if errors == 'strict':
                # Check if the bytes that follow an ESC byte are ESC_END or ESC_ESC
                escaped_parts = packet.split(ESCb)
                error_bytes = [s[0] for s in escaped_parts[1:] if s and s[0] not in (ESC_END, ESC_ESC)]
                if error_bytes:
                    msg = 'Invalid escape sequence ESC-{}'.format(bytes(error_bytes[0:1]))
                    raise SlipEncodingError(msg)
                if len(escaped_parts) > 1 and escaped_parts[-1] == b'':
                    msg = 'Unfinished escape sequence'
                    raise SlipEncodingError(msg)
            if errors == 'replace':
                escaped_parts = packet.split(ESCb)
                join_parts = []
                part = escaped_parts[0]
                for s in escaped_parts[1:]:
                    if s and s[0] not in (ESC_END, ESC_ESC):
                        part += s
                    else:
                        join_parts.append(part)
                if part:
                    join_parts.append(part)
                packet = ESCb.join(join_parts)
                
            if final and self.input_buffer:
                msg = 'Remaining undecoded bytes: {!r}'.format(self.input_buffer)
                self.input_buffer = b''
                raise SlipDecodingError(msg)
                
            return packet.replace(ESC_ENDb, ENDb).replace(ESC_ESCb, ESCb)
        
    def reset(self, final=True):
        self.input_buffer = b''
    
    def getstate(self):
        return 0
    
    def setstate(self, state):
        pass
        
        
encode = partial(SlipEncoder().encode, final=True)
decode = partial(SlipDecoder().decode, final=True)


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

