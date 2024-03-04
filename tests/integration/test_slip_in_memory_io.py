#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

# ruff: noqa: UP035

"""Test using SlipStream with an in-memory bytestream"""

import io
from typing import Generator

import pytest

from sliplib import END, SlipStream


class TestSlipStreamWithBytesIO:
    """Test SlipStream with BytesIO."""

    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        """Setup the test"""
        self.basestream = io.BytesIO()
        self.slipstream = SlipStream(self.basestream)
        yield
        self.basestream.close()

    def test_stream_reading(self) -> None:
        """Test reading from the bytestream"""

        msg_list = [b"hallo", b"bye"]
        self.basestream.write(END + msg_list[0] + END + END + msg_list[1] + END)
        self.basestream.seek(0)
        assert self.slipstream.recv_msg() == msg_list[0]
        assert self.slipstream.recv_msg() == msg_list[1]
        # No more messages
        assert self.slipstream.recv_msg() == b""

    def test_stream_reading_single_bytes(self) -> None:
        """Test reading single bytes from the bytestream"""

        msg_list = [b"hallo", b"bye"]
        self.basestream.write(END + msg_list[0] + END + END + msg_list[1] + END)
        self.basestream.seek(0)
        self.slipstream = SlipStream(self.basestream, 1)
        assert self.slipstream.recv_msg() == msg_list[0]
        assert self.slipstream.recv_msg() == msg_list[1]
        # No more messages
        assert self.slipstream.recv_msg() == b""

    def test_stream_writing(self) -> None:
        """Test writing to the bytestream"""

        msg_list = [b"hallo", b"bye"]
        for msg in msg_list:
            self.slipstream.send_msg(msg)
        assert self.basestream.getvalue() == END + msg_list[0] + END + END + msg_list[1] + END
