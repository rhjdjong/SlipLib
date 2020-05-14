#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

import io
import pytest
from sliplib import SlipStream, END


class TestSlipStreamWithBytesIO:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.basestream = io.BytesIO()
        self.slipstream = SlipStream(self.basestream)
        yield
        self.basestream.close()

    def test_stream_reading(self):
        msg_list = [b'hallo', b'bye']
        self.basestream.write(END + msg_list[0] + END + END + msg_list[1] + END)
        self.basestream.seek(0)
        assert self.slipstream.recv_msg() == msg_list[0]
        assert self.slipstream.recv_msg() == msg_list[1]
        # No more messages
        assert self.slipstream.recv_msg() == b''

    def test_stream_reading_single_bytes(self):
        msg_list = [b'hallo', b'bye']
        self.basestream.write(END + msg_list[0] + END + END + msg_list[1] + END)
        self.basestream.seek(0)
        self.slipstream = SlipStream(self.basestream, 1)
        assert self.slipstream.recv_msg() == msg_list[0]
        assert self.slipstream.recv_msg() == msg_list[1]
        # No more messages
        assert self.slipstream.recv_msg() == b''

    def test_stream_writing(self):
        msg_list = [b'hallo', b'bye']
        for msg in msg_list:
            self.slipstream.send_msg(msg)
        assert self.basestream.getvalue() == END + msg_list[0] + END + END + msg_list[1] + END
