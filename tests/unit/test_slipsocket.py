# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

import pytest

import socket

import sliplib
from sliplib import ProtocolError, SlipSocket, END, ESC


# noinspection PyAttributeOutsideInit,PyUnresolvedReferences
class TestSlipSocket:
    @pytest.fixture(autouse=True, params=[
        socket.AF_INET,
        socket.AF_INET6
    ])
    def setup(self, request):
        self.family = request.param
        self.far_address = socket.getaddrinfo('example.com', 54321, self.family)[0][-1]
        self.near_address = socket.getaddrinfo('localhost', 12345, self.family)[0][-1]
        sock = socket.socket(family=self.family)
        self.slipsocket = SlipSocket(sock)
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
        mocker.patch('sliplib.socket.socket.sendall')
        sliplib.socket.socket.sendall.reset_mock()
        self.slipsocket.send_msg(b'hallo')
        sliplib.socket.socket.sendall.assert_called_once_with(END + b'hallo' + END)
        sliplib.socket.socket.sendall.reset_mock()
        self.slipsocket.send_msg(b'bye')
        sliplib.socket.socket.sendall.assert_called_once_with(END + b'bye' + END)

    def test_receiving_data(self, mocker):
        def socket_data_generator():
            yield END + b'hallo'
            yield END + END
            yield b'bye'
            yield END + END
            yield b''

        mocker.patch('sliplib.socket.socket.recv')
        sliplib.socket.socket.recv.reset_mock()
        sliplib.socket.socket.recv.side_effect = socket_data_generator()
        assert self.slipsocket.recv_msg() == b'hallo'
        # noinspection PyProtectedMember
        sz = sliplib.SlipSocket._chunk_size
        expected_calls = [mocker.call.recv(sz), mocker.call.recv(sz)]
        assert sliplib.socket.socket.recv.mock_calls == expected_calls
        assert self.slipsocket.recv_msg() == b'bye'
        expected_calls += [mocker.call.recv(sz), mocker.call.recv(sz)]
        assert sliplib.socket.socket.recv.mock_calls == expected_calls
        assert self.slipsocket.recv_msg() == b''
        expected_calls += [mocker.call.recv(sz)]
        assert sliplib.socket.socket.recv.mock_calls == expected_calls

    def test_end_of_data_handling(self, mocker):
        def socket_data_generator():
            yield END + b'hallo'
            yield END + END
            yield b'bye'
            yield b''
            yield b''

        mocker.patch('sliplib.socket.socket.recv')
        sliplib.socket.socket.recv.reset_mock()
        sliplib.socket.socket.recv.side_effect = socket_data_generator()
        assert self.slipsocket.recv_msg() == b'hallo'
        assert self.slipsocket.recv_msg() == b'bye'
        assert self.slipsocket.recv_msg() == b''

    def test_exception_on_protocol_error(self, mocker):
        def socket_data_generator():
            yield END + b'hallo' + END + ESC + b'error' + END + b'bye' + END
            yield b'some additional bytes, not relevant'

        mocker.patch('sliplib.socket.socket.recv')
        sliplib.socket.socket.recv.reset_mock()
        sliplib.socket.socket.recv.side_effect = socket_data_generator()
        assert self.slipsocket.recv_msg() == b'hallo'
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b'error',)
        assert self.slipsocket.recv_msg() == b'bye'

    def test_exception_on_protocol_error_in_first_packet(self, mocker):
        def socket_data_generator():
            yield END + ESC + b'error' + END + b'hallo' + END + b'bye' + END
            yield b'some additional bytes, not relevant'

        mocker.patch('sliplib.socket.socket.recv')
        sliplib.socket.socket.recv.reset_mock()
        sliplib.socket.socket.recv.side_effect = socket_data_generator()
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b'error',)
        assert self.slipsocket.recv_msg() == b'hallo'
        assert self.slipsocket.recv_msg() == b'bye'

    def test_exceptions_on_consecutive_invalid_packets(self, mocker):
        def socket_data_generator():
            yield END + b'hallo' + END + ESC + b'error' + END + b'another' + ESC + END + b'bye' + END
            yield b'some additional bytes, not relevant'

        mocker.patch('sliplib.socket.socket.recv')
        sliplib.socket.socket.recv.reset_mock()
        sliplib.socket.socket.recv.side_effect = socket_data_generator()
        assert self.slipsocket.recv_msg() == b'hallo'
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b'error',)
        with pytest.raises(sliplib.ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (b'another' + ESC,)
        assert self.slipsocket.recv_msg() == b'bye'

    def test_accept_method(self, mocker):
        mocker.patch('sliplib.socket.socket.accept')
        sliplib.socket.socket.accept.reset_mock()
        new_socket = sliplib.socket.socket(self.family, socket.SOCK_STREAM)
        sliplib.socket.socket.accept.return_value = (new_socket, self.far_address)
        new_slip_socket, address = self.slipsocket.accept()
        sliplib.socket.socket.accept.assert_called_once()
        assert isinstance(new_slip_socket, SlipSocket)
        assert new_slip_socket.socket is new_socket
        assert address == self.far_address

    @pytest.mark.parametrize('method', [
        attr for attr in dir(socket.socket) if
        callable(getattr(socket.socket, attr)) and (
                attr.startswith('recv') or
                attr.startswith('send') or
                attr in ('dup', 'makefile', 'share')
        )
    ])
    def test_exception_for_not_supported_operations(self, method):
        with pytest.raises(AttributeError):
            getattr(self.slipsocket, method)

    @pytest.mark.parametrize('method', [
        attr for attr in dir(socket.socket) if
        callable(getattr(socket.socket, attr)) and
        not attr.startswith('_') and
        not attr.startswith('recv') and
        not attr.startswith('send') and
        attr not in ('accept', 'dup', 'makefile', 'share')
    ])
    def test_delegated_methods(self, method, mocker):
        mocker.patch.object(sliplib.socket.socket, method)
        getattr(sliplib.socket.socket, method).reset_mock()
        getattr(self.slipsocket, method)()  # Don't care about the arguments
        getattr(sliplib.socket.socket, method).assert_called_once_with()

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


if __name__ == '__main__':
    pytest.main()