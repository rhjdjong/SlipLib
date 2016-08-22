'''
Created on 8 mrt. 2015

@author: Ruud
'''
import unittest

from sliplib import *
from sliplib.slip import END, ESC, ESC_END, ESC_ESC


class EncodingTest(unittest.TestCase):
    def test_empty_message_encoding(self):
        msg = b''
        packet = END+END
        self.assertEqual(encode(msg), packet)
    
    def test_simple_message_encoding(self):
        msg = b'hallo'
        packet = END + msg + END
        self.assertEqual(encode(msg), packet)

    def test_special_character_encoding(self):
        test_list = [(END, ESC+ESC_END),
                     (ESC, ESC+ESC_ESC),
                     (ESC+ESC_END, ESC+ESC_ESC + ESC_END),
                     (ESC+ESC_ESC, ESC+ESC_ESC + ESC_ESC),
                     (ESC+END, ESC+ESC_ESC + ESC+ESC_END),
                     (ESC+ESC, ESC+ESC_ESC + ESC+ESC_ESC),
                     ]
        for msg, p in test_list:
            packet = END + bytes(p) + END
            self.assertEqual(encode(msg), packet,
                             'Encoding failed for {}'.format(msg))


class DecodingTest(unittest.TestCase):
    def test_empty_packet_decoding(self):
        packet = END+END
        self.assertEqual(decode(packet), b'')
        
    def test_single_message_decoding(self):
        msg = b'hallo'
        packet = END + msg + END
        self.assertEqual(decode(packet), msg)
    
    def test_special_character_decoding(self):
        test_list = [(ESC+ESC_ESC, ESC),
                     (ESC+ESC_END, END),
                     (ESC_ESC+ESC+ESC_END, ESC_ESC+END),
                     (ESC_END+ESC+ESC_ESC, ESC_END+ESC),
                     (ESC+ESC_ESC+ESC+ESC_END, ESC+END),
                     (ESC+ESC_END+ESC+ESC_ESC, END+ESC),
                     ]
        for p, msg in test_list:
            packet = END + bytes(p) + END
            self.assertEqual(decode(packet), msg,
                             'Decoding failed for {}'.format(packet))
    
    def test_protocol_error_is_ignored_during_decoding(self):
        test_list = [ESC+b'x',
                     b'abc'+ESC,
                     b'a'+END+b'z',
                     ]
        for msg in test_list:
            packet = END + msg + END
            self.assertEqual(decode(packet), msg)
    
    

class IsValidTest(unittest.TestCase):
    def test_empty_packet_is_valid(self):
        self.assertTrue(is_valid(END+END))
        self.assertTrue(is_valid(b''))
        
    def test_packet_with_single_message_is_valid(self):
        packet = END + b'hallo' + END
        self.assertTrue(is_valid(packet))
    
    
    def test_packet_with_special_character_encoding_is_valid(self):
        test_list = [ESC+ESC_ESC,
                     ESC+ESC_END,
                     ESC_ESC+ESC+ESC_END,
                     ESC_END+ESC+ESC_ESC,
                     ESC+ESC_ESC+ESC+ESC_END,
                     ESC+ESC_END+ESC+ESC_ESC,
                     ]
        for p in test_list:
            packet = END + p + END
            self.assertTrue(is_valid(packet))

    def test_packet_with_protocol_error_is_invalid(self):
        self.assertFalse(is_valid(END+b'a'+END+b'b'+END))
        self.assertFalse(is_valid(ESC+b'x'))
        self.assertFalse(is_valid(b'unfinished'+ESC))
        self.assertFalse(is_valid(b'unfinished'+ESC+END))
    

class DriverTest(unittest.TestCase):
    def setUp(self):
        self.driver = Driver()
    
    def test_single_message_decoding(self):
        msg = b'hallo'
        self.driver.receive(END + msg + END)
        self.assertSequenceEqual(self.driver.messages, [msg])

    def test_message_buffer_is_flushed_after_reading(self):
        msg = b'hallo'
        self.driver.receive(END + msg + END)
        self.assertSequenceEqual(self.driver.messages, [msg])
        self.assertSequenceEqual(self.driver.messages, [])
            
    def test_multi_message_decoding(self):
        msgs = [b'hi', b'there']
        packet = END*2 + msgs[0] + END*5 + msgs[1] + END*7
        self.driver.receive(packet)
        self.assertSequenceEqual(self.driver.messages, msgs)
    
    def test_split_message_decoding(self):
        msg = b'hallo'
        packet = END + msg
        for b in packet:
            self.driver.receive(bytes((b,)))
            self.assertSequenceEqual(self.driver.messages, [])
        self.driver.receive(END)
        self.assertSequenceEqual(self.driver.messages, [msg])
        
    def test_end_of_stream_with_empty_packet(self):
        msg_list = [b'hi', b'there']
        packet = END + msg_list[0] + END + msg_list[1]
        self.driver.receive(packet)
        self.assertSequenceEqual(self.driver.messages, msg_list[:-1])
        self.driver.receive(b'')
        self.assertSequenceEqual(self.driver.messages, [msg_list[-1]])
    
    def test_single_message_encoding(self):
        msg = b'hallo'
        self.driver.send(msg)
        self.assertEqual(self.driver.packets, encode(msg))
    
    def test_multi_message_encoding(self):
        msg_list = [b'hi', b'there']
        for m in msg_list:
            self.driver.send(m)
        self.assertEqual(self.driver.packets, b''.join(encode(m) for m in msg_list))
    
    def test_packet_buffer_is_flushed_after_reading(self):
        msg = b'hallo'
        self.driver.send(msg)
        self.assertEqual(self.driver.packets, encode(msg))
        self.assertEqual(self.driver.packets, b'')
        
    def test_stream_with_errors(self):
        msgs = [b'hallo', b'with'+ESC+b' error', b'with trailing'+ESC,  b'there']
        packet = END + (END*2).join(msgs) + END
        self.driver.receive(packet)
        self.assertSequenceEqual(self.driver.messages, msgs)

        
class DriverStrictTest(unittest.TestCase):
    def setUp(self):
        self.driver = Driver(error='strict')
    
    def test_single_message_decoding(self):
        msg = b'hallo'
        self.driver.receive(END + msg + END)
        self.assertSequenceEqual(self.driver.messages, [msg])

    def test_message_buffer_is_flushed_after_reading(self):
        msg = b'hallo'
        self.driver.receive(END + msg + END)
        self.assertSequenceEqual(self.driver.messages, [msg])
        self.assertSequenceEqual(self.driver.messages, [])
            
    def test_multi_message_decoding(self):
        msgs = [b'hi', b'there']
        packet = END*2 + msgs[0] + END*5 + msgs[1] + END*7
        self.driver.receive(packet)
        self.assertSequenceEqual(self.driver.messages, msgs)
    
    def test_split_message_decoding(self):
        msg = b'hallo'
        packet = END + msg
        for b in packet:
            self.driver.receive(bytes((b,)))
            self.assertSequenceEqual(self.driver.messages, [])
        self.driver.receive(END)
        self.assertSequenceEqual(self.driver.messages, [msg])
        
    def test_end_of_stream_with_empty_packet(self):
        msg_list = [b'hi', b'there']
        packet = END + msg_list[0] + END + msg_list[1]
        self.driver.receive(packet)
        self.assertSequenceEqual(self.driver.messages, msg_list[:-1])
        self.driver.receive(b'')
        self.assertSequenceEqual(self.driver.messages, [msg_list[-1]])
    
    def test_single_message_encoding(self):
        msg = b'hallo'
        self.driver.send(msg)
        self.assertEqual(self.driver.packets, encode(msg))
    
    def test_multi_message_encoding(self):
        msg_list = [b'hi', b'there']
        for m in msg_list:
            self.driver.send(m)
        self.assertEqual(self.driver.packets, b''.join(encode(m) for m in msg_list))
        
    def test_packet_buffer_is_flushed_after_reading(self):
        msg = b'hallo'
        self.driver.send(msg)
        self.assertEqual(self.driver.packets, encode(msg))
        self.assertEqual(self.driver.packets, b'')
        
    def test_stream_with_errors(self):
        msgs = [b'hallo', b'with'+ESC+b' error', b'with trailing'+ESC,  b'there']
        packet = END + (END*2).join(msgs) + END
        with self.assertRaises(ProtocolError) as e:
            self.driver.receive(packet)
            self.assertSequenceEqual(e.args, (b'with'+ESC+b' error', b'with trailing'+ESC))
        self.assertSequenceEqual(self.driver.messages, (msgs[0], msgs[-1]))
            
            
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()