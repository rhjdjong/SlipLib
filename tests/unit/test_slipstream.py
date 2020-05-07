# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import pytest
import io
from unittest.mock import patch, MagicMock
import sliplib
from sliplib import SlipStream, END, ESC, ProtocolError


def test_slip_stream_fails_if_instantiated_with_non_bytestream_argument():
    with pytest.raises(ValueError):
        SlipStream('string is not valid as a bytestream')

# noinspection PyAttributeOutsideInit
class TestSlipStreamWithBytesIO:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.basestream = io.BytesIO()
        # noinspection PyTypeChecker
        self.slipstream = SlipStream(self.basestream)
        yield
        self.slipstream.close()

    def test_stream_creation(self):
        assert self.slipstream.stream is self.basestream

    def test_stream_reading(self):
        msg_list = [b'hallo', b'bye']
        self.basestream.write(END + msg_list[0] + END + END + msg_list[1] + END)
        self.basestream.seek(0)
        assert self.slipstream.recv_msg() == msg_list[0]
        assert self.slipstream.recv_msg() == msg_list[1]
        self.basestream.close()
        # No more messages
        assert self.slipstream.recv_msg() == b''

    def test_stream_writing(self):
        msg_list = [b'hallo', b'bye']
        for msg in msg_list:
            self.slipstream.send_msg(msg)
        assert self.basestream.getvalue() == END + msg_list[0] + END + END + msg_list[1] + END

    @pytest.mark.parametrize('method', [
        'detach', 'getbuffer', 'getvalue', 'peek', 'raw', 'read', 'read1', 'readinto', 'readinto1',
        'readline', 'readlines', 'seek', 'tell', 'truncate', 'write', 'writelines'
    ])
    def test_exception_for_not_supported_operations(self, method):
        with pytest.raises(AttributeError):
            getattr(self.slipstream, method)

    @pytest.mark.parametrize('method', [
        attr for attr in dir(io.BytesIO) if
        not attr.startswith('_') and
        callable(getattr(io.BytesIO, attr)) and
        attr not in (
            'detach', 'getbuffer', 'getvalue', 'read', 'read1', 'readinto', 'readinto1',
            'readline', 'readlines', 'seek', 'tell', 'truncate', 'write', 'writelines')
    ])
    def test_delegated_methods(self, method, mocker):
        # Cannot patch built-in _io.BytesIO, so have to resort to patching the stream attribute in slipstream.
        with patch.object(self.slipstream, 'stream') as mock_stream:
            slipstream_method = getattr(self.slipstream, method)
            slipstream_method()
            getattr(mock_stream, method).assert_called_once_with()


class TestSlipStreamWithFileIO:
    def test_file_writing(self, tmpdir):
        f = tmpdir.mkdir('writing').join('slip.txt')
        fio = f.open(mode='wb')
        s = SlipStream(fio)
        s.send_msg(b'hallo')
        s.send_msg(b'bye')
        s.close()
        assert fio.closed
        assert f.read_binary() == END + b'hallo' + END + END + b'bye' + END

    def test_file_reading(self, tmpdir):
        f = tmpdir.mkdir('reading').join('slip.txt')
        f.write_binary(END + b'hallo' + END + END + b'bye' + END)
        fio = f.open(mode='rb')
        s = SlipStream(fio)
        assert s.recv_msg() == b'hallo'
        assert s.recv_msg() == b'bye'
        assert s.recv_msg() == b''
        s.close()
        assert fio.closed

    @pytest.mark.parametrize('method', [
        'detach', 'getbuffer', 'getvalue', 'peek', 'raw', 'read', 'read1', 'readinto', 'readinto1',
        'readline', 'readlines', 'seek', 'tell', 'truncate', 'write', 'writelines'
    ])
    def test_exception_for_not_supported_operations(self, method):
        self.slipstream = SlipStream(io.BufferedIOBase())
        with pytest.raises(AttributeError):
            getattr(self.slipstream, method)
        self.slipstream.close()

    # noinspection PyUnresolvedReferences
    @pytest.mark.parametrize('method', [
        attr for attr in dir(io.BytesIO) if
        not attr.startswith('_') and
        callable(getattr(io.BytesIO, attr)) and
        attr not in (
                'detach', 'getbuffer', 'getvalue', 'read', 'read1', 'readinto', 'readinto1',
                'readline', 'readlines', 'seek', 'tell', 'truncate', 'write', 'writelines')
    ])
    def test_delegated_methods(self, method, mocker):
        self.slipstream = SlipStream(io.BufferedIOBase())
        mocker.patch.object(sliplib.io.BufferedIOBase, method)
        getattr(sliplib.io.BufferedIOBase, method).reset_mock()
        getattr(self.slipstream, method)()  # Don't care about the arguments
        getattr(sliplib.io.BufferedIOBase, method).assert_called_once_with()
        self.slipstream.close()

    def test_with_statement_and_iteration_on_file(self, tmpdir):
        f = tmpdir.mkdir('reading').join('slip.txt')
        f.write_binary(END + b'hallo' + END + END + b'bye' + END)
        with open(f, mode='rb') as stream:
            s = SlipStream(stream)
            expected = (b'hallo', b'bye')
            for exp, act in zip(expected, s):
                assert exp == act

    def test_syntax_error_in_file_contents_is_detected_during_iteration(self, tmpdir):
        f = tmpdir.mkdir('reading').join('slip.txt')
        f.write_binary(END + b'hallo' + ESC + END + END + b'bye' + END)
        with open(f, mode='rb') as stream:
            s = SlipStream(stream)
            with pytest.raises(ProtocolError):
                for msg in s:
                    pass
            for msg in s:
                assert msg == b'bye'
                break
