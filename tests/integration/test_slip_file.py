#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

# pylint: disable=relative-beyond-top-level

"""Test using SlipStream with a buffered file"""

from sliplib import SlipStream, encode

from .test_data import BaseFileTest, data


class TestBufferedFileAccess(BaseFileTest):
    """Test buffered SLIP file access"""

    def test_reading_slip_file(self) -> None:
        """Test reading encoded SLIP messages"""

        self.filepath.write_bytes(b"".join(encode(msg) for msg in data))
        with self.filepath.open(mode="rb") as f:
            slipstream = SlipStream(f)
            for exp, act in zip(data, slipstream):
                assert exp == act

    def test_writing_slip_file(self) -> None:
        """Test writing encoded SLIP messages"""

        with self.filepath.open(mode="wb") as f:
            slipstream = SlipStream(f)
            for msg in data:
                slipstream.send_msg(msg)
        assert self.filepath.read_bytes() == b"".join(encode(msg) for msg in data)
