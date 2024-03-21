# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.


"""
This module contains the tests for the low-level SLIP functions and classes.
"""
from typing import Generator

import pytest

from sliplib import END, ESC, ESC_END, ESC_ESC, Driver, ProtocolError, decode, encode


class TestEncoding:
    """Test encoding of SLIP messages."""

    def test_empty_message_encoding(self) -> None:
        """Empty message should result in an empty packet."""
        msg = b""
        packet = END + END
        assert encode(msg) == packet

    def test_simple_message_encoding(self) -> None:
        """A simple message without special bytes should be surrounded with END bytes."""
        msg = b"hallo"
        packet = END + msg + END
        assert encode(msg) == packet

    def test_single_byte_encoding(self) -> None:
        """Verify that single bytes are encoded correctly"""
        msg = b"x"
        packet = END + msg + END
        assert encode(msg) == packet

    def test_message_with_zero_byte_decoding(self) -> None:
        """A message that contains a NULL byte must be encoded correctly."""
        msg = b"a\0b"
        packet = END + msg + END
        assert encode(msg) == packet

    @pytest.mark.parametrize(
        ("msg", "packet"),
        [
            (END, ESC + ESC_END),
            (ESC, ESC + ESC_ESC),
            (ESC + ESC_END, ESC + ESC_ESC + ESC_END),
            (ESC + ESC_ESC, ESC + ESC_ESC + ESC_ESC),
            (ESC + END, ESC + ESC_ESC + ESC + ESC_END),
            (ESC + ESC, ESC + ESC_ESC + ESC + ESC_ESC),
        ],
    )
    def test_special_character_encoding(self, msg: bytes, packet: bytes) -> None:
        """Messages with special bytes should encode these according to the specification."""
        assert encode(msg) == END + packet + END


class TestDecoding:
    """Test decoding of SLIP packets."""

    def test_empty_packet_decoding(self) -> None:
        """An empty packet should result in an empty message."""
        packet = END + END
        assert decode(packet) == b""

    def test_simple_message_decoding(self) -> None:
        """A packet without the special escape sequences should result in a message without special bytes."""
        msg = b"hallo"
        packet = END + msg + END
        assert decode(packet) == msg

    def test_single_byte_decoding(self) -> None:
        """A packet with a single byte between END bytes must be decoded correctly."""
        msg = b"x"
        packet = END + msg + END
        assert decode(packet) == msg

    def test_message_with_zero_byte_decoding(self) -> None:
        """A packet that contains a NULL byte must be decoded correctly."""
        msg = b"a\0b"
        packet = END + msg + END
        assert decode(packet) == msg

    @pytest.mark.parametrize(
        ("packet", "msg"),
        [
            (ESC + ESC_ESC, ESC),
            (ESC + ESC_END, END),
            (ESC_ESC + ESC + ESC_END, ESC_ESC + END),
            (ESC_END + ESC + ESC_ESC, ESC_END + ESC),
            (ESC + ESC_ESC + ESC + ESC_END, ESC + END),
            (ESC + ESC_END + ESC + ESC_ESC, END + ESC),
        ],
    )
    def test_special_character_decoding(self, packet: bytes, msg: bytes) -> None:
        """A packet with special escape sequences should result in a message with the appropriate special bytes."""
        packet = END + packet + END
        assert decode(packet) == msg

    @pytest.mark.parametrize(
        "packet",
        [
            ESC + b"x",
            b"abc" + ESC,
            b"a" + END + b"z",
        ],
    )
    def test_invalid_packet_raises_protocol_error(self, packet: bytes) -> None:
        """A packet with an invalid escape sequence should result in a ProtocolError."""
        packet = END + packet + END
        with pytest.raises(ProtocolError) as exc_info:
            decode(packet)
        assert exc_info.value.args == (packet,)


class TestDriver:
    """Tests for the Driver class."""

    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        """Test preparation."""
        self.driver = Driver()
        yield
        del self.driver

    def test_message_encoding(self) -> None:
        """Test message encoding."""
        msg = b"hallo"
        packet = self.driver.send(msg)
        assert packet == END + msg + END

    def test_single_message_decoding(self) -> None:
        """Test decoding of a byte string with a single packet."""
        msg = b"hallo"
        packet = encode(msg)
        self.driver.receive(packet)
        assert self.driver.get(timeout=0.5) == msg

    def test_multi_message_decoding(self) -> None:
        """Test decoding of a byte string with multiple packets."""
        msgs = [b"hi", b"there"]
        packet = END + msgs[0] + END + msgs[1] + END
        self.driver.receive(packet)
        assert self.driver.get(timeout=0.5) == msgs[0]
        assert self.driver.get(timeout=0.5) == msgs[1]

    def test_multiple_end_bytes_are_ignored_during_decoding(self) -> None:
        """Test decoding of a byte string with multiple packets."""
        msgs = [b"hi", b"there"]
        packet = END + END + msgs[0] + END + END + END + END + msgs[1] + END + END + END
        self.driver.receive(packet)
        assert self.driver.get(timeout=0.5) == msgs[0]
        assert self.driver.get(timeout=0.5) == msgs[1]

    def test_split_message_decoding(self) -> None:
        """Test that receives only returns the message after the complete packet has been received.

        The message contains a NULL byte to test the correct handling of this when single bytes are received.
        """
        msg = b"hallo\0bye"
        packet = END + msg
        for byte_ in packet:
            self.driver.receive(byte_)
            assert self.driver.get(block=False) is None
        self.driver.receive(END)
        assert self.driver.get(timeout=0.5) == msg

    def test_flush_buffers_with_empty_packet(self) -> None:
        """Test that receiving an empty byte string results in completion of the pending packet."""
        expected_msg_list = [b"hi", b"there"]
        packet = END + expected_msg_list[0] + END + expected_msg_list[1]
        self.driver.receive(packet)
        assert self.driver.get(timeout=0.5) == expected_msg_list[0]
        assert self.driver.get(block=False) is None
        self.driver.receive(b"")
        assert self.driver.get(timeout=0.5) == expected_msg_list[1]

    @pytest.mark.parametrize("message", [b"with" + ESC + b" error", b"with trailing" + ESC])
    def test_packet_with_protocol_error(self, message: bytes) -> None:
        """Test that an invalid bytes sequence in the packet results in a protocol error."""
        packet = END + message + END
        self.driver.receive(packet)
        with pytest.raises(ProtocolError) as exc_info:
            self.driver.get(timeout=0.5)
        assert exc_info.value.args == (message,)

    def test_messages_before_invalid_packets(self) -> None:
        """Test that the messages that were received before an invalid packet can be retrieved."""
        msgs = [b"hallo", b"with" + ESC + b" error"]
        packet = END + END.join(msgs) + END
        self.driver.receive(packet)
        assert self.driver.get(timeout=0.5) == msgs[0]
        with pytest.raises(ProtocolError) as exc_info:
            self.driver.get(timeout=0.5)
        assert exc_info.value.args == (msgs[1],)

    def test_messages_after_invalid_packets(self) -> None:
        """Test that the messages that were received before an invalid packet can be retrieved."""
        msgs = [b"with" + ESC + b" error", b"bye"]
        packet = END + END.join(msgs) + END
        self.driver.receive(packet)
        with pytest.raises(ProtocolError) as exc_info:
            self.driver.get(timeout=0.5)
        assert exc_info.value.args == (msgs[0],)
        assert self.driver.get(timeout=0.5) == msgs[1]

    def test_subsequent_packets_with_wrong_escape_sequence(self) -> None:
        """Test that each invalid packet results in a protocol error."""
        msgs = [
            b"hallo",
            b"with" + ESC + b" error",
            b"in the middle",
            b"with trailing" + ESC,
            b"bye",
        ]
        packet = END + END.join(msgs) + END
        self.driver.receive(packet)
        assert self.driver.get(timeout=0.5) == msgs[0]
        with pytest.raises(ProtocolError) as exc_info:
            self.driver.get(timeout=0.5)
        assert exc_info.value.args == (msgs[1],)
        assert self.driver.get(timeout=0.5) == msgs[2]
        with pytest.raises(ProtocolError) as exc_info:
            self.driver.get(timeout=0.5)
        assert exc_info.value.args == (msgs[3],)
        assert self.driver.get(timeout=0.5) == msgs[4]
