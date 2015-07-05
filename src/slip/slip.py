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


class SlipEncoder():
    encode_map = {END: ESC_END, ESC: ESC_ESC}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encoded_bytes = bytearray()

    def encode(self, obj, errors=None, final=False):
        try:
            self.errors
        except AttributeError:
            self.errors = 'strict'
        if errors is not None:
            self.errors = errors

        if not isinstance(obj, collections.abc.Iterable):
            obj = (obj,)
        
        if not self.encoded_bytes:
            self.encoded_bytes.append(END)
                
        for b in bytes(obj):
            if b not in (END, ESC):
                self.encoded_bytes.append(b)
            else:
                self.encoded_bytes.append(ESC)
                self.encoded_bytes.append(self.encode_map[b])
        
        if final:
            try:
                if len(self.encoded_bytes) > 1:
                    self.encoded_bytes.append(END)
                else:
                    self.encoded_bytes.clear()
                return bytes(self.encoded_bytes)
            finally:
                self.reset()

    def reset(self):
        self.encoded_bytes.clear()
    
    def getstate(self):
        return 0
    
    def setstate(self, state):
        pass
        

class SlipDecoder():        
    class State(IntEnum):
        idle = 0
        normal = 1
        escaped = 2
        finished = 3
        error = 4
    
    decode_map = {ESC_END: END, ESC_ESC: ESC}
       
    def _decode_replace_errors_strict(self, b):
        try:
            self.decoded_bytes.append(self.decode_map[b])
        except KeyError:
            error_msg = r'Invalid slip ESC sequence: ESC-\x{:02x}'.format(b)
            raise SlipEncodingError(error_msg)
    
    def _decode_replace_errors_replace(self, b):
        self.decoded_bytes.append(self.decode_map.get(b, b))
    
    def _decode_replace_errors_ignore(self, b):
        try:
            self.decoded_bytes.append(self.decode_map[b])
        except KeyError:
            self.decoded_bytes.append(ESC)
            self.decoded_bytes.append(b)

    
    _decode_function_map = {
        'strict': _decode_replace_errors_strict,
        'replace': _decode_replace_errors_replace,
        'ignore': _decode_replace_errors_ignore,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_buffer = bytearray()
        self.decoded_bytes = bytearray()
        self.reset(True)

    def _idle_handler(self, b, errors):
        # Wait for a non-END byte
        if b != END:
            if b == ESC:
                self.state = self.State.escaped
            else:
                self.state = self.State.normal
                self.decoded_bytes.append(b)
    
    def _normal_handler(self, b, errors):
        if b == ESC:
            self.state = self.State.escaped
        elif b == END:
            self.state = self.State.finished
        else:
            self.decoded_bytes.append(b)
    
    def _escaped_handler(self, b, errors):
        # Decode the next character following and ESC byte.
        # Exact handling depends on the 'errors' setting
        self._decode_function_map[errors](self, b)
        self.state = self.State.normal
    
    def _error_handler(self, b, errors):
        # Error recovery: skip to the next END byte
        if b == END:
            self.state = self.State.idle

    _handle_map = {
        State.idle: _idle_handler,
        State.normal: _normal_handler,
        State.escaped: _escaped_handler,
        State.error: _error_handler,
    }

    def decode(self, obj, errors=None, final=False):
        if errors is None:
            try:
                errors = self.errors
            except AttributeError:
                errors = 'strict'
        
        if not isinstance(obj, collections.abc.Iterable):
            obj = (obj,)
        self.input_buffer.extend(bytes(obj))
        
        try:
            for b in self.input_buffer:
                self.scan_pos += 1
                self._handle_map[self.state](self, b, errors)
                if self.state == self.State.finished:
                    break
        except SlipEncodingError:
            self.state = self.State.error
            self.decoded_bytes.clear()
            self.reset(final)
            raise
        
        try:
            if final:
                if self.state == self.State.finished and any(b != END for b in
                                                             self.input_buffer[self.scan_pos:]):
                    raise SlipDecodingError('Input not completely decoded. Remaining: {!r}'.
                                            format(self.input_buffer))
                elif self.state == self.State.escaped:
                    raise SlipDecodingError('Incomplete input. Unfinished ESC sequence.')
        except SlipDecodingError:
            self.decoded_bytes.clear()
            raise
        else:
            if self.state == self.State.finished or final:
                packet = bytes(self.decoded_bytes)
                self.decoded_bytes.clear()
                return packet
        finally:
            self.reset(final)

        
    def reset(self, final=True):
        if final:
            # Clear input buffer
            self.input_buffer.clear()
            self.state = self.State.idle
        else:
            del self.input_buffer[:self.scan_pos]
        self.scan_pos = 0
        if self.state == self.State.finished:
            self.state = self.State.idle
    
    def getstate(self):
        return self.state.value
    
    def setstate(self, state):
        self.state = self.State(state)
        
        
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

