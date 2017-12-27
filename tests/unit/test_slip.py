# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import pytest

from sliplib import *


class TestEncoding:
    def test_empty_message_encoding(self):
        msg = b''
        packet = END + END
        assert encode(msg) == packet

    def test_simple_message_encoding(self):
        msg = b'hallo'
        packet = END + msg + END
        assert encode(msg) == packet

    @pytest.mark.parametrize("msg,packet", [
        (END, ESC + ESC_END),
        (ESC, ESC + ESC_ESC),
        (ESC + ESC_END, ESC + ESC_ESC + ESC_END),
        (ESC + ESC_ESC, ESC + ESC_ESC + ESC_ESC),
        (ESC + END, ESC + ESC_ESC + ESC + ESC_END),
        (ESC + ESC, ESC + ESC_ESC + ESC + ESC_ESC),
    ])
    def test_special_character_encoding(self, msg, packet):
        assert encode(msg) == END + packet + END


# noinspection PyPep8Naming
class TestDecoding:
    def test_empty_packet_decoding(self):
        packet = END + END
        assert decode(packet) == b''

    def test_simple_message_decoding(self):
        msg = b'hallo'
        packet = END + msg + END
        assert decode(packet) == msg

    @pytest.mark.parametrize("packet,msg", [
        (ESC + ESC_ESC, ESC),
        (ESC + ESC_END, END),
        (ESC_ESC + ESC + ESC_END, ESC_ESC + END),
        (ESC_END + ESC + ESC_ESC, ESC_END + ESC),
        (ESC + ESC_ESC + ESC + ESC_END, ESC + END),
        (ESC + ESC_END + ESC + ESC_ESC, END + ESC),
    ])
    def test_special_character_decoding(self, packet, msg):
        packet = END + packet + END
        assert decode(packet) == msg

    @pytest.mark.parametrize("packet", [
        ESC + b'x',
        b'abc' + ESC,
        b'a' + END + b'z',
    ])
    def test_protocol_error_raises_ProtocolError(self, packet):
        packet = END + packet + END
        with pytest.raises(ProtocolError) as exc_info:
            decode(packet)
        assert exc_info.value.args == (packet.strip(END),)


# noinspection PyAttributeOutsideInit,PyPep8Naming
class TestDriver:
    @pytest.fixture(autouse=True)
    def driver(self):
        self.driver = Driver()
        yield
        del self.driver

    def test_message_encoding(self):
        msg = b'hallo'
        packet = self.driver.send(msg)
        assert packet == END + msg + END

    def test_single_message_decoding(self):
        msg = b'hallo'
        packet = encode(msg)
        msg_list = self.driver.receive(packet)
        assert msg_list == [msg]

    def test_multi_message_decoding(self):
        msgs = [b'hi', b'there']
        packet = END + END + msgs[0] + END + END + END + msgs[1] + END + END + END
        assert self.driver.receive(packet) == msgs

    def test_split_message_decoding(self):
        msg = b'hallo'
        packet = END + msg
        for b in packet:
            assert self.driver.receive(bytes((b,))) == []
        assert self.driver.receive(END) == [msg]

    def test_flush_buffers_with_empty_packet(self):
        expected_msg_list = [b'hi', b'there']
        packet = END + expected_msg_list[0] + END + expected_msg_list[1]
        assert self.driver.receive(packet) == expected_msg_list[:1]
        assert self.driver.receive(b'') == expected_msg_list[1:]

    def test_stream_with_errors_raises_ProtocolError_for_invalid_packet(self):
        msgs = [b'hallo', b'with' + ESC + b' error', b'with trailing' + ESC, b'there']
        packet = END + END.join(msgs) + END
        with pytest.raises(ProtocolError) as exc_info:
            self.driver.receive(packet)
        assert self.driver.messages == msgs[:1]
        assert exc_info.value.args == (msgs[1],)
        with pytest.raises(ProtocolError) as exc_info:
            self.driver.flush()
        assert self.driver.messages == []
        assert exc_info.value.args == (msgs[2],)
        assert self.driver.flush() == msgs[3:]


if __name__ == '__main__':
    pytest.main()
