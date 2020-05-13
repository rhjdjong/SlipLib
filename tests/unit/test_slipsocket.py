# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import socket
import pytest
import sliplib
from sliplib import ProtocolError, SlipSocket, END, ESC

socket_methods = [
    attr for attr in dir(socket.socket)
    if callable(getattr(socket.socket, attr)) and
       not attr.startswith('_')
]

delegated_methods = [
    attr for attr in socket_methods
    if not (attr.startswith('recv') or
            attr.startswith('send') or
            attr in ('accept', 'dup', 'makefile', 'share'))
]

not_delegated_methods = [
    attr for attr in socket_methods
    if not attr in delegated_methods and
       attr != 'accept'
]


class TestSlipSocket:
    @pytest.fixture(autouse=True, params=[
        (socket.AF_INET,
         ('93.184.216.34', 54321),  # example.com IPv4 address
         ('127.0.0.1', 12345)  # localhost IPv4 address
         ),
        (socket.AF_INET6,
         ('2606:2800:220:1:248:1893:25c8:1946', 54321, 0, 0),  # example.com IPv6 address
         ('::1', 12345, 0, 0)  # localhost IPv6 address
        )
    ])
    def setup(self, request, mocker):
        self.family, self.far_address, self.near_address = request.param
        self.sock_mock = mocker.Mock(spec=socket.socket(family=self.family), family=self.family,
                                     type=socket.SOCK_STREAM, proto=0)
        self.slipsocket = SlipSocket(self.sock_mock)
        yield
        self.slipsocket.close()
        del self.slipsocket

    def test_slipsocket_instantiation(self):
        assert self.slipsocket.family == self.family
        assert self.slipsocket.type == socket.SOCK_STREAM

    def test_slipsocket_instantiation_from_socket(self):
        sock = socket.socket(family=self.family)
        slipsocket = SlipSocket(sock=sock)
        assert slipsocket.socket is sock

    # noinspection PyPep8Naming
    def test_slipsocket_requires_TCP_socket(self):
        sock = socket.socket(family=self.family, type=socket.SOCK_DGRAM)
        with pytest.raises(ValueError):
            SlipSocket(sock)

    def test_sending_data(self, mocker):
        self.slipsocket.send_msg(b'hallo')
        self.slipsocket.send_msg(b'bye')
        self.sock_mock.sendall.assert_has_calls([
            mocker.call(END + b'hallo' + END),
            mocker.call(END + b'bye' + END)
        ])

    def test_receiving_data(self, mocker):
        def socket_data_generator():
            yield END + b'hallo'
            yield END + END
            yield b'bye'
            yield END + END
            yield b''

        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        assert self.slipsocket.recv_msg() == b'hallo'
        # noinspection PyProtectedMember
        sz = sliplib.SlipSocket._chunk_size
        expected_calls = [mocker.call.recv(sz), mocker.call.recv(sz)]
        self.sock_mock.recv.assert_has_calls(expected_calls)
        assert self.slipsocket.recv_msg() == b'bye'
        expected_calls += [mocker.call.recv(sz), mocker.call.recv(sz)]
        self.sock_mock.recv.assert_has_calls(expected_calls)
        assert self.slipsocket.recv_msg() == b''
        expected_calls += [mocker.call.recv(sz)]
        self.sock_mock.recv.assert_has_calls(expected_calls)

    def test_end_of_data_handling(self, mocker):
        def socket_data_generator():
            yield END + b'hallo'
            yield END + END
            yield b'bye'
            yield b''
            yield b''

        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        assert self.slipsocket.recv_msg() == b'hallo'
        assert self.slipsocket.recv_msg() == b'bye'
        assert self.slipsocket.recv_msg() == b''
        sz = sliplib.SlipSocket._chunk_size
        expected_calls = [mocker.call.recv(sz)] * 4
        self.sock_mock.recv.assert_has_calls(expected_calls)

    def test_exception_on_protocol_error(self, mocker):
        def socket_data_generator():
            yield END + b'hallo' + END + ESC + b'error' + END + b'bye' + END
            yield b'some additional bytes, not relevant'

        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        assert self.slipsocket.recv_msg() == b'hallo'
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b'error',)
        assert self.slipsocket.recv_msg() == b'bye'

    def test_exception_on_protocol_error_in_first_packet(self, mocker):
        def socket_data_generator():
            yield END + ESC + b'error' + END + b'hallo' + END + b'bye' + END
            yield b'some additional bytes, not relevant'

        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b'error',)
        assert self.slipsocket.recv_msg() == b'hallo'
        assert self.slipsocket.recv_msg() == b'bye'

    def test_exceptions_on_consecutive_invalid_packets(self, mocker):
        def socket_data_generator():
            yield END + b'hallo' + END + ESC + b'error' + END + b'another' + ESC + END + b'bye' + END
            yield b'some additional bytes, not relevant'

        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        assert self.slipsocket.recv_msg() == b'hallo'
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b'error',)
        with pytest.raises(sliplib.ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (b'another' + ESC,)
        assert self.slipsocket.recv_msg() == b'bye'

    def test_accept_method(self, mocker):
        new_socket = mocker.Mock(spec=socket.socket(family=self.family), family=self.family, type=socket.SOCK_STREAM,
                                 proto=0)
        self.sock_mock.accept = mocker.Mock(return_value=(new_socket, self.far_address))
        new_slip_socket, address = self.slipsocket.accept()
        self.sock_mock.accept.assert_called_once_with()
        assert isinstance(new_slip_socket, SlipSocket)
        assert new_slip_socket.socket is new_socket
        assert address == self.far_address

    @pytest.mark.parametrize('method', not_delegated_methods)
    def test_exception_for_not_supported_operations(self, method):
        with pytest.raises(AttributeError):
            getattr(self.slipsocket, method)

    @pytest.mark.parametrize('method', delegated_methods)
    def test_delegated_methods(self, method, mocker):
        setattr(self.sock_mock, method, mocker.Mock())
        slipsocket_method = getattr(self.slipsocket, method)
        slipsocket_method()  # Don't care about the arguments
        mocked_method = getattr(self.sock_mock, method)
        mocked_method.assert_called_once_with()

    @pytest.mark.parametrize('attr', [
        'family', 'type', 'proto'
    ])
    def test_read_only_attribute(self, attr):
        assert getattr(self.slipsocket, attr) == getattr(self.slipsocket.socket, attr)
        with pytest.raises(AttributeError):
            setattr(self.slipsocket, attr, "some value")

    def test_create_connection(self, mocker):
        mocker.patch('sliplib.socket.create_connection')
        sliplib.socket.create_connection.reset_mock()
        new_sock = socket.socket(self.family)
        sliplib.socket.create_connection.return_value = new_sock
        sock = SlipSocket.create_connection(self.far_address)
        assert isinstance(sock, SlipSocket)
        assert sock.socket is new_sock
        sliplib.socket.create_connection.assert_called_once_with(self.far_address, None, None)

    def test_slip_socket_iteration(self, mocker):
        def socket_data_generator():
            yield END + b'hallo'
            yield END + END
            yield b'bye'
            yield END + END
            yield b''
        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        expected = (b'hallo', b'bye')
        for exp, act in zip(expected, self.slipsocket):
            assert exp == act

if __name__ == '__main__':
    pytest.main()
