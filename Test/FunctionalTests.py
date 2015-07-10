'''
Created on 28 jun. 2015

@author: Ruud
'''
import unittest
import socketserver
import multiprocessing

from slip import slip

END_byte = bytes((slip.END,))
ESC_byte = bytes((slip.ESC,))
ESC_ESC_byte = bytes((slip.ESC_ESC,))
ESC_END_byte = bytes((slip.ESC_END,))

class SlipRequestHandler(socketserver.BaseRequestHandler):
    ## Custom encode and decode methods,
    ## to be independent of the functions being tested
    @staticmethod
    def encode(msg):
        msg = msg.replace(ESC_byte, ESC_byte+ESC_ESC_byte)\
            .replace(END_byte, ESC_byte+ESC_END_byte)
        return END_byte + msg + END_byte
    
    @staticmethod
    def decode(packet):
        return packet.strip(END_byte)\
            .replace(ESC_byte+ESC_END_byte, END_byte)\
            .replace(ESC_byte+ESC_ESC_byte, ESC_byte)
    
    def handle(self):
        self.slip_buffer = bytearray()
        while True:
            data = self.request.recv(1024)
            if not data:
                break
            self.slip_buffer.extend(data)
            self.slip_buffer = self.slip_buffer.lstrip(END_byte)
            while END_byte in self.slip_buffer:
                packet, self.slip_buffer = self.slip_buffer.split(END_byte, maxsplit=1)
                self.slip_buffer = self.slip_buffer.lstrip(END_byte)
                msg = self.decode(packet)
                self.request.sendall(self.encode(msg.upper()))
        

class SlipServerProcess(multiprocessing.Process):
    def __init__(self, pipe=None, **kwargs):
        super().__init__(**kwargs)
        self.pipe = pipe
        self.daemon = True
        
    def run(self):
        self.server = socketserver.TCPServer(('127.0.0.1', 0), SlipRequestHandler)
        self.pipe.send(self.server.server_address)
        self.server.serve_forever()
        
       
class FunctionalTests(unittest.TestCase):
    def setUp(self):
        ear, mouth = multiprocessing.Pipe()
        self.server_process = SlipServerProcess(pipe=mouth)
        self.server_process.start()
        self.server_address = ear.recv()
    
    def tearDown(self):
        self.server_process.terminate()
        self.server_process.join(0.5)
    
    def test_basic_encode_decode_capability(self):
        # John needs uses to communicate with an application via a TCP connection.
        # The application uses the SLIP protocol to send and receive data packets.
        # The application returns the packet, but with all ascii characters in uppercase.

        # John decides to use the slip 'encode' and 'decode' functions to
        # communicate with the remote application
    
        # First John imports the slip package
        import slip
        
        # John has read in the documentation that the slip package
        # adds codecs with encoding and decoding capability
        import codecs
        encode = codecs.getencoder('slip')
        decode = codecs.getdecoder('slip')
        
        # The he sets up a TCP connection to the remote application
        import socket
        conn = socket.create_connection(self.server_address)
        
        # John first tries a few simple examples
        msg = b'hello'
        conn.sendall(encode(msg))
        response = conn.recv(1024)
        self.assertEqual(decode(response), b'HELLO')
        
        # John is curious to see if multiple packets sent at the same time
        # are handled correctly
        first_packet = b'hello'
        second_packet = b'world'
        third_packet = b'!'
        msg = encode(first_packet) + encode(second_packet) + encode(third_packet)
        conn.sendall(msg)
        response = bytearray()
        while len(response) < len(msg):
            response.extend(conn.recv(1024))
        received_packets = [p for p in response.split(END_byte) if p]
        self.assertEqual(len(received_packets), 3)
        self.assertEqual(decode(received_packets[0], ), b'HELLO')
        self.assertEqual(decode(received_packets[1]), b'WORLD')
        self.assertEqual(decode(received_packets[2]), b'!')
        
        # John knows about the SLIP special characters END and ESC.
        # He wants to see if these are handled.
        msg = b'hello' + END_byte + b'slip'
        conn.sendall(encode(msg))
        response = conn.recv(1024)
        self.assertEqual(decode(response), b'HELLO' + END_byte + b'SLIP')
        
        msg = b'hello' + ESC_byte + b'slip'
        conn.sendall(encode(msg))
        response = conn.recv(1024)
        self.assertEqual(decode(response), b'HELLO' + ESC_byte + b'SLIP')
        
        msg = b'hello' + ESC_byte + END_byte + b'slip'
        conn.sendall(encode(msg))
        response = conn.recv(1024)
        self.assertEqual(decode(response), b'HELLO' + ESC_byte + END_byte + b'SLIP')

        msg = b'hello' + END_byte + ESC_byte + b'slip'
        conn.sendall(encode(msg))
        response = conn.recv(1024)
        self.assertEqual(decode(response), b'HELLO' + END_byte + ESC_byte + b'SLIP')
        
    def test_slip_stream_reader_and_writer(self):
        # John recognizes that explicitly using the 'encode' and 'decode'
        # function is tedious and error-prone.
        # He decides to experiment with the SlipStreamReader and
        # SlipStreamWriter classes that are also provided by the slip package

        # First John imports the slip package
        import slip
        
        # Then he again sets up a TCP connection to the remote application
        import socket
        conn = socket.create_connection(self.server_address)
        conn_file = conn.makefile('rwb', buffering=0)
        
        # John has read in the documentation that the slip package
        # provides a stream reader and stream writer
        import codecs
        reader = codecs.getreader('slip')(conn_file)
        writer = codecs.getwriter('slip')(conn_file)
        
        # He repeats the earlier tests
        # John first tries a few simple examples
        msg = b'hello'
        writer.write(msg)
        response = reader.read()
        self.assertEqual(response, b'HELLO')
        
        # John is curious to see if multiple packets sent at the same time
        # are handled correctly
        first_packet = b'hello'
        second_packet = b'world'
        third_packet = b'!'
        writer.writelines([first_packet, second_packet, third_packet])
        received_packets = reader.readlines(3)
        self.assertSequenceEqual(received_packets, [b'HELLO', b'WORLD', b'!'])
        
        # John knows about the SLIP special characters END and ESC.
        # He wants to see if these are handled.
        msg = b'hello' + END_byte + b'slip'
        writer.write(msg)
        response = reader.read()
        self.assertEqual(response, b'HELLO' + END_byte + b'SLIP')
        
        msg = b'hello' + ESC_byte + b'slip'
        writer.write(msg)
        response = reader.read()
        self.assertEqual(response, b'HELLO' + ESC_byte + b'SLIP')
        
        msg = b'hello' + ESC_byte + END_byte + b'slip'
        writer.write(msg)
        response = reader.read()
        self.assertEqual(response, b'HELLO' + ESC_byte + END_byte + b'SLIP')

        msg = b'hello' + END_byte + ESC_byte + b'slip'
        writer.write(msg)
        response = reader.read()
        self.assertEqual(response, b'HELLO' + END_byte + ESC_byte + b'SLIP')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()