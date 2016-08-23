'''
Created on 29 jun. 2015

@author: Ruud de Jong
'''

import re
from threading import Lock

"""These constants represent the special SLIP bytes."""

END = b'\xc0'
ESC = b'\xdb'
ESC_END = b'\xdc'
ESC_ESC = b'\xdd'


class ProtocolError(ValueError):
    pass


def encode(msg: bytes) -> bytes:
    """encode(msg) -> SLIP-encoded message.
    """
    return END + msg.replace(ESC, ESC+ESC_ESC).replace(END, ESC+ESC_END) + END

def decode(packet: bytes) -> bytes:
    """decode(packet) -> message from SLIP-encoded packet
    """
    return packet.strip(END).replace(ESC+ESC_END, END).replace(ESC+ESC_ESC, ESC)

def is_valid(packet: bytes) -> bool:
    """is_valid(packet) -> indicates if the packet's contents conform to the SLIP specification.
    
    A packet is valid if:
    * It contains no END bytes other than leading and/or trailing END bytes, and
    * All ESC bytes are followed by an ESC_END or ESC_ESC byte.  
    """ 
    packet = packet.strip(END)
    return not (END in packet or
                packet.endswith(ESC) or
                re.search(ESC+b'[^'+ESC_END+ESC_ESC+b']', packet))


class Driver():
    def __init__(self, error='ignore'):
        self.error = error
        self._recv_buffer = b''
        self._packets = []
        self._messages = []
        self._recvlock = Lock()
        self._sendlock = Lock()
    
    def send(self, data: bytes):
        """send(data). Encode data in a SLIP send.
        
        Encoded data is buffered. By reading the attribute
        'packets', the buffer is flushed.
        """
        with self._sendlock:
            self._packets.append(encode(data))
        
    @property
    def packets(self) -> bytes:
        """packets -> Read and flush the packet buffer.
        """
        with self._sendlock:
            result = b''.join(self._packets)
            self._packets = []
        return result

    def receive(self, data: bytes):
        """receive(data). Handle received SLIP-encoded data.
        
        Extracts packets from data, and decodes them. The resulting messages
        are buffered, and can be retrieved by reading the attribute 'messages'.
        """
        
        # Empty data indicates that the data reception is complete.
        # To force a buffer flush, an END byte is added, so that the
        # current contents of _recv_buffer will form a complete message.
        if not data:
            data = END
        
        self._recv_buffer += data
        
        # The following situations can occur:
        #
        #  1) _recv_buffer empty or contains only END bytes --> no new packets
        #  2) _recv_buffer contains non-END bytes --> new packets from data
        
        # Strip leading END bytes from _recv_buffer to avoid empty _packets.
        self._recv_buffer = self._recv_buffer.lstrip(END)
        if not self._recv_buffer:
            return
        
        # The _recv_buffer is split on sequences of one or more END bytes.
        # The trailing element from the split operation is a possibly incomplete
        # packet; this element is therefore used as the new _recv_buffer.
        # If _recv_buffer has one or more trailing END bytes, then the last element,
        # and therefore the new _recv_buffer, is an empty bytes object.
        packets = re.split(END+b'+', self._recv_buffer)
        self._recv_buffer = packets.pop(-1)

        # Add the decoded _messages to the message buffer.
        with self._recvlock:
            if self.error == 'strict':
                # With strict error checking, only decode valid packets.
                # If any invalid packets are present, a ProtocolError exception is raised,
                # indicating the invalid packets.
                invalid_packets = []
                for p in packets:
                    if is_valid(p):
                        self._messages.append(decode(p))
                    else:
                        invalid_packets.append(p)
                if invalid_packets:
                    raise ProtocolError(invalid_packets)
            else:
                # For non-strict error checking, ignore protocol violations.
                self._messages.extend(decode(p) for p in packets)
        
    @property
    def messages(self) -> [bytes]:
        """messages -> Read and flush the message buffer"""
        with self._recvlock:
            result = self._messages
            self._messages = []            
        return result

    
                
        
        
        
        