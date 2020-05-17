#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

# pylint: disable=relative-beyond-top-level

"""Test using SlipStream with an unbuffered file"""

from sliplib import encode, SlipStream
from .test_data import data, BaseFileTest

class TestUnbufferedFileAccess(BaseFileTest):
    """Test unbuffered SLIP file access."""

    def test_reading_slip_file(self):
        """Test reading SLIP-encoded message"""

        self.filepath.write_bytes(b''.join(encode(msg) for msg in data))
        with self.filepath.open(mode='rb', buffering=0) as f:
            slipstream = SlipStream(f)
            for exp, act in zip(data, slipstream):
                assert exp == act


    def test_writing_slip_file(self):
        """Test writing SLIP-encoded messages"""

        with self.filepath.open(mode='wb', buffering=0) as f:
            slipstream = SlipStream(f)
            for msg in data:
                slipstream.send_msg(msg)
        assert self.filepath.read_bytes() == b''.join(encode(msg) for msg in data)
