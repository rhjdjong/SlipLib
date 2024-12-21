#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""Test using SlipStream with a buffered file"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib

from sliplib import END, SlipStream, encode, use_leading_end_byte

data = [
    b"line 1",
    b"line with embedded\nnewline",
    b"last line",
]


def test_reading_slip_file(tmp_path: pathlib.Path, *, receive_leading_end_byte: bool) -> None:
    """Test reading encoded SLIP messages"""
    prefix = END if receive_leading_end_byte else b""
    data_file = tmp_path / "data.txt"
    data_file.write_bytes(b"".join(prefix + encode(msg) + END for msg in data))
    with data_file.open(mode="rb") as f:
        with use_leading_end_byte(receive_leading_end_byte):
            slipstream = SlipStream(f)
        for expected, actual in zip(data, slipstream):
            assert expected == actual


def test_writing_slip_file(tmp_path: pathlib.Path, *, send_leading_end_byte: bool) -> None:
    """Test writing encoded SLIP messages"""
    prefix = END if send_leading_end_byte else b""
    data_file = tmp_path / "data.txt"
    with data_file.open(mode="wb") as f:
        with use_leading_end_byte(send_leading_end_byte):
            slipstream = SlipStream(f)
        for msg in data:
            slipstream.send_msg(msg)
    assert data_file.read_bytes() == b"".join(prefix + encode(msg) + END for msg in data)


def test_reading_slip_file_unbuffered(tmp_path: pathlib.Path, *, receive_leading_end_byte: bool) -> None:
    """Test reading SLIP-encoded message"""
    prefix = END if receive_leading_end_byte else b""
    data_file = tmp_path / "data.txt"
    data_file.write_bytes(b"".join(prefix + encode(msg) + END for msg in data))
    with data_file.open(mode="rb", buffering=0) as f:
        with use_leading_end_byte(receive_leading_end_byte):
            slipstream = SlipStream(f)
        for expected, actual in zip(data, slipstream):
            assert expected == actual


def test_writing_slip_file_unbuffered(tmp_path: pathlib.Path, *, send_leading_end_byte: bool) -> None:
    """Test writing SLIP-encoded messages"""
    prefix = END if send_leading_end_byte else b""
    data_file = tmp_path / "data.txt"
    with data_file.open(mode="wb", buffering=0) as f:
        with use_leading_end_byte(send_leading_end_byte):
            slipstream = SlipStream(f)
        for msg in data:
            slipstream.send_msg(msg)
    assert data_file.read_bytes() == b"".join(prefix + encode(msg) + END for msg in data)
