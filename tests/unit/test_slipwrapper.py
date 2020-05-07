# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import pytest
from sliplib import SlipWrapper

class TestSlipWrapper:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.slipwrapper = SlipWrapper('not a valid byte stream')
        yield

    def test_slip_wrapper_recv_msg_is_not_implemented(self):
        with pytest.raises(NotImplementedError):
            _ = self.slipwrapper.recv_msg()

    def test_slip_wrapper_send_msg_is_not_implemented(self):
        with pytest.raises(NotImplementedError):
            self.slipwrapper.send_msg(b'oops')

    def test_slip_wrapper_closed_is_not_implemented(self):
        with pytest.raises(NotImplementedError):
            self.slipwrapper.closed



