'''
Created on 8 mrt. 2015

@author: Ruud
'''
import unittest
import io
from itertools import chain

from slip.slip import END, ESC, ESC_END, ESC_ESC, SlipEncodingError, SlipDecodingError
import codecs

encode = codecs.getencoder('slip')
decode = codecs.getdecoder('slip')
reader = codecs.getreader('slip')
writer = codecs.getwriter('slip')
inc_encoder = codecs.getincrementalencoder('slip')
inc_decoder = codecs.getincrementaldecoder('slip')


class EncodingDecodingTest(unittest.TestCase):
    def test_empty_message_encoding(self):
        msg = b''
        self.assertEqual(encode(msg), b'')
        
    def test_empty_message_decoding(self):
        packet=b''
        self.assertEqual(decode(packet), b'')

    def test_simple_encoding_decoding(self):
        msg = b'hello'
        packet = bytes(chain((END,), msg, (END,)))
        self.assertEqual(encode(msg), packet)
        self.assertEqual(decode(packet), msg)

    def test_encoding_decoding_with_embedded_END(self):
        msg = bytes((END,))
        packet = bytes((END, ESC, ESC_END, END))
        self.assertEqual(encode(msg), packet)
        self.assertEqual(decode(packet), msg)
        
    def test_encoding_decoding_with_embedded_ESC(self):
        msg = bytes((ESC,))
        packet = bytes((END, ESC, ESC_ESC, END))
        self.assertEqual(encode(msg), packet)
        self.assertEqual(decode(packet), msg)
    
    def test_invalid_encoding_with_bare_END(self):
        packet = bytes(chain((END,), b'left', (END,), b'right', (END,)))
        with self.assertRaises(SlipDecodingError):
            m = decode(packet)
            self.fail("Got decoded message {!r}".format(m))
        with self.assertRaises(SlipDecodingError):
            m = decode(packet)
            self.fail("Got decoded message {!r}".format(m))
        with self.assertRaises(SlipDecodingError):
            m = decode(packet)
            self.fail("Got decoded message {!r}".format(m))
    
    def test_invalid_encoding_with_invalid_ESC_sequence(self):
        packet = bytes(chain((END,), b'left', (ESC,), b'Xright', (END,)))
        with self.assertRaises(SlipEncodingError):
            m = decode(packet)
            self.fail("Got decoded message {!r}".format(m))
        self.assertEqual(decode(packet, 'ignore'), bytes(chain(b'left', (ESC,), b'Xright')))
        self.assertEqual(decode(packet, 'replace'), b'leftXright')


class SlipIncrementalEncodingDecodingTest(unittest.TestCase):
    def setUp(self):
        self.encoder = codecs.getincrementalencoder('slip')().encode
        self.decoder = codecs.getincrementaldecoder('slip')().decode
        
    def test_empty_message_encoding(self):
        msg = b''
        self.assertEqual(self.encoder(msg, final=True), b'')
    
    def test_empty_message_decoding(self):
        packet=b''
        self.assertEqual(self.decoder(packet, final=True), b'')
        
    def test_simple_encoding_decoding(self):
        msg = b'hello'
        packet = bytes(chain((END,), msg, (END,)))
        self.assertEqual(self.encoder(msg, final=True), packet)
        self.assertEqual(self.decoder(packet), msg)

    def test_encoding_decoding_with_embedded_END(self):
        msg = bytes((END,))
        packet = bytes((END, ESC, ESC_END, END))
        self.assertEqual(self.encoder(msg, final=True), packet)
        self.assertEqual(self.decoder(packet), msg)
        
    def test_encoding_decoding_with_embedded_ESC(self):
        msg = bytes((ESC,))
        packet = bytes((END, ESC, ESC_ESC, END))
        self.assertEqual(self.encoder(msg, final=True), packet)
        self.assertEqual(self.decoder(packet), msg)
    
    def test_invalid_encoding_with_bare_END(self):
        packet = bytes(chain((END,), b'left', (END,), b'right', (END,)))
        with self.assertRaises(SlipDecodingError):
            m = decode(packet, final=True)
            self.fail("Got decoded message {!r}".format(m))
            self.decoder(packet, final=True)
        with self.assertRaises(SlipDecodingError):
            m = self.decoder(packet, final=True, errors='ignore')
            self.fail("Got decoded message {!r}".format(m))
        with self.assertRaises(SlipDecodingError):
            m = self.decoder(packet, final=True, errors='replace')
            self.fail("Got decoded message {!r}".format(m))
    
    def test_invalid_encoding_with_invalid_ESC_sequence(self):
        packet = bytes(chain((END,), b'left', (ESC,), b'Xright', (END,)))
        with self.assertRaises(SlipEncodingError):
            m = self.decoder(packet)
            self.fail("Got decoded message {!r}".format(m))
        self.assertEqual(self.decoder(packet, errors='ignore'), bytes(chain(b'left', (ESC,), b'Xright')))
        self.assertEqual(self.decoder(packet, errors='replace'), b'leftXright')

    def test_decoder_is_reset_after_decoding_escape_error(self):
        packet = bytes(chain((END,), b'left', (ESC,), b'Xright', (END,)))
        with self.assertRaises(SlipEncodingError):
            m = decode(packet)
            self.fail("Got decoded message {!r}".format(m))
        msg = b'hello'
        packet = bytes(chain((END,), msg, (END,)))
        self.assertEqual(self.decoder(packet), msg)
        
    def test_decoder_is_reset_after_remaining_bytes_error(self):
        packet = bytes(chain((END,), b'left', (END,), b'right', (END,)))
        with self.assertRaises(SlipDecodingError):
            m = self.decoder(packet, final=True)
            self.fail("Got decoded message {!r}".format(m))
        msg = b'hello'
        packet = bytes(chain((END,), msg, (END,)))
        self.assertEqual(self.decoder(packet), msg)
        
    def test_decoder_is_reset_after_unfinished_escape_error(self):
        packet = bytes(chain((END,), b'left', (ESC,)))
        with self.assertRaises(SlipEncodingError):
            m = self.decoder(packet, final=True)
            self.fail("Got decoded message {!r}".format(m))
        msg = b'hello'
        packet = bytes(chain((END,), msg, (END,)))
        self.assertEqual(self.decoder(packet), msg)
    
    def test_decoder_waits_for_END_after_unfinished_escpae_error(self):
        packet = bytes(chain((END,), b'left', (ESC,), b'wrong'))
        self.assertIsNone(self.decoder(packet))
        packet = bytes(chain(b'noise', (END,), b'right', (END,)))
        with self.assertRaises(SlipEncodingError):
            m = self.decoder(packet)
            self.fail("Got decoded message {!r}".format(m))
        self.assertEqual(self.decoder(b'', final=True), b'right')

    def test_simple_incremental_encoding_and_decoding(self):
        msg = b'hello'
        for b in msg:
            self.encoder(b, final=False)
        packet = self.encoder(b'', final=True)
        self.assertEqual(packet, bytes(chain((END,), msg, (END,))))
        decoded_msg = bytearray()
        for b in packet:
            m = self.decoder(b, final=False)
            if m:
                decoded_msg.extend(m)
        m = self.decoder(b'', final=True)
        if m:
            decoded_msg.extend(m)
        self.assertEqual(decoded_msg, msg)


class SlipReaderWriterTest(unittest.TestCase):
    def setUp(self):
        self.buffer = io.BytesIO()
        self.writer = writer(self.buffer)
        self.reader = reader(self.buffer)
        
    def test_empty_message_encoding(self):
        msg = b''
        self.writer.write(msg)
        self.assertEqual(self.buffer.getvalue(), b'')
    
    def test_empty_message_decoding(self):
        packet=b''
        self.buffer.write(packet)
        self.reader.seek(0)       
        self.assertEqual(self.reader.read(), b'')
        
    def test_simple_encoding_decoding(self):
        msg = b'hello'
        packet = bytes(chain((END,), msg, (END,)))
        self.writer.write(msg)
        self.assertEqual(self.buffer.getvalue(), packet)
        self.reader.seek(0)
        self.assertEqual(self.reader.read(), msg)

    def test_encoding_decoding_with_embedded_END(self):
        msg = bytes((END,))
        packet = bytes((END, ESC, ESC_END, END))
        self.writer.write(msg)
        self.assertEqual(self.writer.getvalue(), packet)
        self.reader.seek(0)
        self.assertEqual(self.reader.read(), msg)
        
    def test_encoding_decoding_with_embedded_ESC(self):
        msg = bytes((ESC,))
        packet = bytes((END, ESC, ESC_ESC, END))
        self.writer.write(msg)
        self.assertEqual(self.buffer.getvalue(), packet)
        self.reader.seek(0)
        self.assertEqual(self.reader.read(), msg)
    
    def test_encoding_with_bare_END(self):
        packet = bytes(chain((END,), b'left', (END,), b'right', (END,)))
        self.buffer.write(packet)
        self.reader.seek(0)
        self.assertEqual(self.reader.read(), b'left')
        self.assertEqual(self.reader.read(), b'right')
    
    def test_invalid_encoding_with_invalid_ESC_sequence(self):
        packet = bytes(chain((END,), b'left', (ESC,), b'Xright', (END,)))
        self.buffer.write(packet)
        self.reader.seek(0)
        with self.assertRaises(SlipEncodingError):
            m = self.reader.read()
            self.fail("Got decoded message {!r}".format(m))
        self.reader.errors = 'ignore'
        self.reader.seek(0)
        self.assertEqual(self.reader.read(), bytes(chain(b'left', (ESC,), b'Xright')))
        self.reader.errors = 'replace'
        self.reader.seek(0)
        self.assertEqual(self.reader.read(), b'leftXright')

    def test_decoder_is_reset_after_decoding_escape_error(self):
        packet = bytes(chain((END,), b'left', (ESC,), b'Xright', (END,)))
        self.buffer.write(packet)
        self.reader.seek(0)
        with self.assertRaises(SlipEncodingError):
            m = self.reader.read()
            self.fail("Got decoded message {!r}".format(m))
        msg = b'hello'
        pos = self.reader.tell()
        packet = bytes(chain((END,), msg, (END,)))
        self.buffer.write(packet)
        self.reader.seek(pos)
        self.assertEqual(self.reader.read(), msg)
        
    def test_decoder_is_reset_after_remaining_bytes_error(self):
        packet = bytes(chain((END,), b'left', (END,), b'right', (END,)))
        self.buffer.write(packet)
        self.reader.seek(0)
        self.assertEqual(self.reader.read(), b'left')
        self.assertEqual(self.reader.read(), b'right')
        msg = b'hello'
        pos = self.reader.tell()
        packet = bytes(chain((END,), msg, (END,)))
        self.buffer.write(packet)
        self.reader.seek(pos)
        self.assertEqual(self.reader.read(), msg)
        
    def test_decoder_is_reset_after_unfinished_escape_error(self):
        packet = bytes(chain((END,), b'left', (ESC,)))
        self.buffer.write(packet)
        self.reader.seek(0)
        with self.assertRaises(SlipEncodingError):
            m = self.reader.read()
            self.fail("Got decoded message {!r}".format(m))
        msg = b'hello'
        pos = self.reader.tell()
        packet = bytes(chain((END,), msg, (END,)))
        self.buffer.write(packet)
        self.reader.seek(pos)
        self.assertEqual(self.reader.read(), msg)

    def test_slip_writelines(self):
        msg_list = [b'one', b'two', b'three']
        packet = bytes(chain((END,), b'one', (END,),
                             (END,), b'two', (END,),
                             (END,), b'three', (END,)))
        self.writer.writelines(msg_list)
        self.assertEqual(self.writer.getvalue(), packet)
    
    def test_slip_readlines(self):
        msg_list = [b'one', b'two', b'three']
        packet = bytes(chain((END,), b'one', (END,),
                             (END,), b'two', (END,),
                             (END,), b'three', (END,)))
        self.buffer.write(packet)
        self.reader.seek(0)
        self.assertSequenceEqual(self.reader.readlines(3), msg_list)
    
            
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()