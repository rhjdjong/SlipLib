# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import io
import warnings
import pytest
from sliplib import SlipStream, END, ESC, ProtocolError


def test_slip_stream_fails_if_instantiated_with_non_io_stream_argument():
    with pytest.raises(TypeError):
        SlipStream('string is not valid as a bytestream')


def test_slip_stream_fails_if_instantiated_with_non_bytestream_argument():
    with pytest.raises(TypeError):
        SlipStream(io.StringIO())


class TestSlipStreamBasics:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.stream_mock = mocker.Mock(spec_set=('read', 'write', 'readable', 'writable'))
        self.stream_mock.read = mocker.Mock()
        self.stream_mock.write = mocker.Mock()
        self.slipstream = SlipStream(self.stream_mock)
        yield

    def test_slipstream_creation(self):
        assert self.slipstream.stream is self.stream_mock

    @pytest.mark.parametrize('rbl, wbl', [(True, True), (True, False), (False, True), (False, False)])
    def test_slipstream_readable_and_writable_attributes(self, rbl, wbl):
        self.stream_mock.configure_mock(readable=rbl, writable=wbl)
        assert self.slipstream.readable == rbl
        assert self.slipstream.writable == wbl

    def test_slipstream_reading(self, mocker):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.read.side_effect = (END + msg_list[0] + END + END + msg_list[1] + END, b'')
        assert self.slipstream.recv_msg() == msg_list[0]
        assert self.slipstream.recv_msg() == msg_list[1]
        # No more messages
        assert self.slipstream.recv_msg() == b''
        assert self.stream_mock.read.mock_calls == [mocker.call(io.DEFAULT_BUFFER_SIZE)] * 2

    def test_slipstream_reading_single_bytes(self, mocker):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.read.side_effect = list(END + msg_list[0] + END + END + msg_list[1] + END) + [b'']
        self.slipstream = SlipStream(self.stream_mock, 1)
        assert self.slipstream.recv_msg() == msg_list[0]
        assert self.slipstream.recv_msg() == msg_list[1]
        # No more messages
        assert self.slipstream.recv_msg() == b''
        assert self.stream_mock.read.mock_calls == [mocker.call(1)] * 13

    def test_slipstream_writing(self, mocker):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.write.side_effect = (len(END + msg_list[0] + END), len(END + msg_list[1] + END))
        for msg in msg_list:
            self.slipstream.send_msg(msg)
        assert self.stream_mock.write.mock_calls == [
            mocker.call(END + msg_list[0] + END),
            mocker.call(END + msg_list[1] + END)
        ]

    def test_slipstream_writing_single_bytes(self, mocker):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.write.return_value = 1
        for msg in msg_list:
            self.slipstream.send_msg(msg)
        encoded_messages = (END + msg_list[0] + END, END + msg_list[1] + END)
        call_list = [mocker.call(enc_msg[i:]) for enc_msg in encoded_messages for i in range(len(enc_msg))]
        assert self.stream_mock.write.mock_calls == call_list

    def test_iterating_over_slipstream(self):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.read.side_effect = (END + msg_list[0] + END + END + msg_list[1] + END, b'')
        for i, msg in enumerate(self.slipstream):
            assert msg_list[i] == msg

    def verify_error_recovery(self, msg_list):
        assert self.slipstream.recv_msg() == msg_list[0]
        with pytest.raises(ProtocolError):
            self.slipstream.recv_msg()
        assert self.slipstream.recv_msg() == msg_list[1]

    def test_recovery_from_protocol_error(self):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.read.side_effect = (END + msg_list[0] + END + ESC + END + msg_list[1] + END, b'')
        self.verify_error_recovery(msg_list)

    def test_recovery_from_protocol_error_with_unbuffered_reads(self):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.read.side_effect = list(END + msg_list[0] + END + ESC + END + msg_list[1] + END) + [b'']
        self.slipstream = SlipStream(self.stream_mock, 1)
        self.verify_error_recovery(msg_list)

    def verify_error_recovery_during_iteration(self, msg_list):
        received_message = []
        with pytest.raises(ProtocolError):
            for msg in self.slipstream:
                received_message.append(msg)
        assert received_message == msg_list[:1]
        for msg in self.slipstream:
            received_message.append(msg)
        assert received_message == msg_list

    def test_recovery_from_protocol_error_during_iteration(self):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.read.side_effect = (END + msg_list[0] + END + ESC + END + msg_list[1] + END, b'')
        self.verify_error_recovery_during_iteration(msg_list)

    def test_recovery_from_protocol_error_during_iteration_with_unbuffered_reads(self):
        msg_list = [b'hallo', b'bye']
        self.stream_mock.read.side_effect = list(END + msg_list[0] + END + ESC + END + msg_list[1] + END) + [b'']
        self.slipstream = SlipStream(self.stream_mock, 1)
        self.verify_error_recovery_during_iteration(msg_list)


# Testing delegated methods.
# This will be removed due to deprecation of delegating methods to the wrapped stream.

# Use the io.BytesIO methods for testing
not_delegated_methods = [attr for attr in dir(io.BytesIO) if attr.startswith('read') and attr != 'readable'] +\
                        [attr for attr in dir(io.BytesIO) if attr.startswith('write') and attr != 'writable'] +\
                        [
                            'detach', 'flushInput', 'flushOutput', 'getbuffer', 'getvalue', 'peek', 'raw',
                            'reset_input_buffer', 'reset_output_buffer', 'seek', 'seekable', 'tell', 'truncate'
                        ]

delegated_methods = [
    attr for attr in dir(io.BytesIO) if
    not attr.startswith('_') and
    callable(getattr(io.BytesIO, attr)) and
    attr not in not_delegated_methods and
    attr not in ('readable', 'writable')
]


class TestDeprecatedMethodDelegation:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        warnings.simplefilter('always')
        self.stream_mock = mocker.Mock(spec_set=['read', 'write'] + delegated_methods)
        self.slipstream = SlipStream(self.stream_mock)
        yield
        warnings.simplefilter('default')

    @pytest.mark.parametrize('method', delegated_methods)
    def test_delegated_methods(self, method):
        with warnings.catch_warnings(record=True) as w:
            slipstream_method = getattr(self.slipstream, method)
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "will be removed in version 1.0" in str(w[0].message)
        slipstream_method()
        getattr(self.stream_mock, method).assert_called_once_with()

    @pytest.mark.parametrize('method', not_delegated_methods)
    def test_exception_for_not_supported_operations(self, method):
        with pytest.raises(AttributeError):
            getattr(self.slipstream, method)
