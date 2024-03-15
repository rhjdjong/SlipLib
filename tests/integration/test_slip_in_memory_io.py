#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.


"""Test using SlipStream with an in-memory bytestream"""

import io
from typing import Generator

import pytest

from sliplib import END, SlipStream


class TestSlipStreamWithBytesIO:
    """Test SlipStream with BytesIO."""

    msg_list = (b"hallo", b"bye")

    @pytest.fixture
    def empty_stream(self) -> Generator[io.BytesIO, None, None]:
        stream = io.BytesIO()
        yield stream
        stream.close()

    @pytest.fixture
    def filled_stream(self, empty_stream: io.BytesIO) -> io.BytesIO:
        empty_stream.seek(0)
        empty_stream.write(END + self.msg_list[0] + END + END + self.msg_list[1] + END)
        empty_stream.seek(0)
        return empty_stream

    def test_stream_reading(self, filled_stream: io.BytesIO) -> None:
        """Test reading from the bytestream"""
        slipstream = SlipStream(filled_stream)
        assert slipstream.recv_msg() == self.msg_list[0]
        assert slipstream.recv_msg() == self.msg_list[1]
        # No more messages
        assert slipstream.recv_msg() == b""

    def test_stream_reading_single_bytes(self, filled_stream: io.BytesIO) -> None:
        """Test reading single bytes from the bytestream"""

        slipstream = SlipStream(filled_stream, 1)
        assert slipstream.recv_msg() == self.msg_list[0]
        assert slipstream.recv_msg() == self.msg_list[1]
        # No more messages
        assert slipstream.recv_msg() == b""

    def test_stream_writing(self, empty_stream: io.BytesIO) -> None:
        """Test writing to the bytestream"""
        slipstream = SlipStream(empty_stream)
        for msg in self.msg_list:
            slipstream.send_msg(msg)
        assert empty_stream.getvalue() == END + self.msg_list[0] + END + END + self.msg_list[1] + END
