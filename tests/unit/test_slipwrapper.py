# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.


"""Tests for SlipWrapper."""

import pytest

from sliplib import SlipWrapper


class TestSlipWrapper:
    """Basic tests for SlipWrapper."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Prepare the test."""
        self.slipwrapper = SlipWrapper("not a valid byte stream")
        self.subwrapper = type("SubSlipWrapper", (SlipWrapper,), {})(None)  # Dummy subclass without implementation

    def test_slip_wrapper_recv_bytes_is_not_implemented(self) -> None:
        """Verify that calling recv_msg on a SlipWrapper instance that does not implement read_bytes fails."""
        with pytest.raises(NotImplementedError):
            _ = self.slipwrapper.recv_msg()
        with pytest.raises(NotImplementedError):
            _ = self.subwrapper.recv_msg()

    def test_slip_wrapper_send_bytes_is_not_implemented(self) -> None:
        """Verify that calling send_msg on a SlipWrapper instance that does not implement send_bytes fails."""
        with pytest.raises(NotImplementedError):
            self.slipwrapper.send_msg(b"oops")
        with pytest.raises(NotImplementedError):
            self.subwrapper.send_msg(b"oops")
