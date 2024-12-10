# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.


"""Tests for SlipWrapper."""

import pytest

from sliplib import SlipWrapper


class TestSlipWrapper:
    """Basic tests for SlipWrapper."""

    def test_slip_wrapper_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            SlipWrapper("just a random byte stream")  # type: ignore [abstract]

    def test_slip_wrapper_cannot_be_subclassed_without_concrete_implementations(self) -> None:
        with pytest.raises(TypeError):
            type("SubSlipWrapper", (SlipWrapper,), {})(None)  # Dummy subclass without implementation
