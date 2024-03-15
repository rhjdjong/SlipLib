#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""Test using SlipStream with a buffered file"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    import pathlib

import pytest

from sliplib import SlipStream, encode

data = [
    b"line 1",
    b"line with embedded\nnewline",
    b"last line",
]


@pytest.fixture
def scrap_file(tmp_path: pathlib.Path) -> Generator[pathlib.Path, None, None]:
    testdir = tmp_path / "slip"
    testdir.mkdir()
    filepath = testdir / "data.txt"
    yield filepath
    filepath.unlink()


@pytest.fixture
def readfile(scrap_file: pathlib.Path) -> pathlib.Path:
    scrap_file.write_bytes(b"".join(encode(msg) for msg in data))
    return scrap_file


@pytest.fixture
def writefile(scrap_file: pathlib.Path) -> pathlib.Path:
    return scrap_file


def test_reading_slip_file(readfile: pathlib.Path) -> None:
    """Test reading encoded SLIP messages"""
    with readfile.open(mode="rb") as f:
        slipstream = SlipStream(f)
        for expected, actual in zip(data, slipstream):
            assert expected == actual


def test_writing_slip_file(writefile: pathlib.Path) -> None:
    """Test writing encoded SLIP messages"""
    with writefile.open(mode="wb") as f:
        slipstream = SlipStream(f)
        for msg in data:
            slipstream.send_msg(msg)
    assert writefile.read_bytes() == b"".join(encode(msg) for msg in data)


def test_reading_slip_file_unbuffered(readfile: pathlib.Path) -> None:
    """Test reading SLIP-encoded message"""
    with readfile.open(mode="rb", buffering=0) as f:
        slipstream = SlipStream(f)
        for expected, actual in zip(data, slipstream):
            assert expected == actual


def test_writing_slip_file_unbuffered(writefile: pathlib.Path) -> None:
    """Test writing SLIP-encoded messages"""
    with writefile.open(mode="wb", buffering=0) as f:
        slipstream = SlipStream(f)
        for msg in data:
            slipstream.send_msg(msg)
    assert writefile.read_bytes() == b"".join(encode(msg) for msg in data)
