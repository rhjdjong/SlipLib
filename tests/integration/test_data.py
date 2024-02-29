#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

# pylint: disable=attribute-defined-outside-init
# pylint: disable=too-few-public-methods

"""Common data for file-related tests"""
import pathlib

import pytest

data = [
    b'line 1',
    b'line with embedded\nnewline',
    b'last line',
]


class BaseFileTest:
    """Base class for filebased SLIP tests."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: pathlib.Path) -> None:
        """Prepare the test."""
        testdir = tmp_path / "slip"
        testdir.mkdir()
        self.filepath = testdir / "read.txt"
