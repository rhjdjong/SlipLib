#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

from sliplib import encode, SlipStream

data = [
    b'line 1',
    b'line with embedded\nnewline',
    b'last line',
]


def test_reading_slip_file(tmp_path):
    d = tmp_path / "slip"
    d.mkdir()
    p = d / "read.txt"
    p.write_bytes(b''.join(encode(msg) for msg in data))
    with p.open(mode='rb') as f:
        s = SlipStream(f)
        for exp, act in zip(data, s):
            assert exp == act


def test_writing_slip_file(tmp_path):
    d = tmp_path / "slip"
    d.mkdir()
    p = d / "write.txt"
    with p.open(mode='wb') as f:
        s = SlipStream(f)
        for msg in data:
            s.send_msg(msg)
    assert p.read_bytes() == b''.join(encode(msg) for msg in data)
