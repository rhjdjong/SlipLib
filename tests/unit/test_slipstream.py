# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import pytest
import io
import sliplib
from sliplib import SlipStream, END


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

    # Cannot test delegated methods in this way, because py.test complains with
    #    TypeError: can't set attributes of built-in/extension type '_io.BytesIO'
    #
    # noinspection PyUnresolvedReferences
    @pytest.mark.skip(reason="Cannot patch attributes of io.BytesIO")
    @pytest.mark.parametrize('method', [
        attr for attr in dir(io.BytesIO) if
        not attr.startswith('_') and
        callable(getattr(io.BytesIO, attr)) and
        attr not in (
            'detach', 'getbuffer', 'getvalue', 'read', 'read1', 'readinto', 'readinto1',
            'readline', 'readlines', 'seek', 'tell', 'truncate', 'write', 'writelines')
    ])
    def test_delegated_methods(self, method, mocker):
        mocker.patch.object(sliplib.io.BytesIO, method)
        getattr(sliplib.io.BytesIO, method).reset_mock()
        getattr(self.slipstream, method)()  # Don't care about the arguments
        getattr(sliplib.io.BytesIO, method).assert_called_once_with()


class TestSlipStreamWithFileIO:
    def test_file_writing(self, tmpdir):
        f = tmpdir.mkdir('writing').join('slip.txt')
        s = SlipStream(f.open(mode='wb'))
        s.send_msg(b'hallo')
        s.send_msg(b'bye')
        s.close()
        assert f.read_binary() == END + b'hallo' + END + END + b'bye' + END

    def test_file_reading(self, tmpdir):
        f = tmpdir.mkdir('reading').join('slip.txt')
        f.write_binary(END + b'hallo' + END + END + b'bye' + END)
        s = SlipStream(f.open(mode='rb'))
        assert s.recv_msg() == b'hallo'
        assert s.recv_msg() == b'bye'
        assert s.recv_msg() == b''
        s.close()

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
