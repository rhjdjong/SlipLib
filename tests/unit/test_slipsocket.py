# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

# pylint: disable=attribute-defined-outside-init
# pylint: disable=too-many-public-methods

"""Tests for SlipSocket"""

import socket
import warnings

import pytest
import sliplib
from sliplib import ProtocolError, SlipSocket, END, ESC

SOCKET_METHODS = [attr for attr in dir(socket.socket) if
                  callable(getattr(socket.socket, attr)) and not attr.startswith('_')]

EXPLICITLY_EXPOSED_SOCKET_METHODS = (
    'accept',
    'bind',
    'close',
    'connect',
    'connect_ex',
    'getpeername',
    'getsockname',
    'listen',
    'shutdown',
)

DELEGATED_METHODS = tuple(
    attr for attr in SOCKET_METHODS
    if not (
        attr.startswith('recv') or attr.startswith('send') or
        attr in ('dup', 'makefile', 'share') or
        attr in EXPLICITLY_EXPOSED_SOCKET_METHODS
    )
)

NOT_DELEGATED_METHODS = tuple(
    attr for attr in SOCKET_METHODS if attr not in DELEGATED_METHODS and attr not in EXPLICITLY_EXPOSED_SOCKET_METHODS
)


class TestSlipSocket:
    """Tests for SlipSocket"""

    @pytest.fixture(autouse=True, params=[
        (socket.AF_INET,  # pylint: disable=no-member
         ('93.184.216.34', 54321),  # example.com IPv4 address
         ('127.0.0.1', 12345)  # localhost IPv4 address
         ),
        (socket.AF_INET6,  # pylint: disable=no-member
         ('2606:2800:220:1:248:1893:25c8:1946', 54321, 0, 0),  # example.com IPv6 address
         ('::1', 12345, 0, 0)  # localhost IPv6 address
         )
    ])
    def setup(self, request, mocker):
        """Prepare the test."""

        self.family, self.far_address, self.near_address = request.param
        self.sock_mock = mocker.Mock(spec=socket.socket(family=self.family), family=self.family,
                                     type=socket.SOCK_STREAM, proto=0)  # pylint: disable=no-member
        self.slipsocket = SlipSocket(self.sock_mock)
        yield
        self.sock_mock.close()
        del self.slipsocket

    def test_slipsocket_instantiation(self):
        """Test that the slipsocket has been created properly."""
        assert self.slipsocket.family == self.family
        assert self.slipsocket.type == socket.SOCK_STREAM  # pylint: disable=no-member
        assert self.slipsocket.proto == 0
        assert self.slipsocket.socket is self.sock_mock

    def test_slipsocket_requires_tcp_socket(self):
        """Test that non-TCP sockets are rejected."""
        self.sock_mock.configure_mock(type=socket.SOCK_DGRAM)  # pylint: disable=no-member
        with pytest.raises(ValueError):
            SlipSocket(self.sock_mock)

    def test_sending_data(self, mocker):
        """Test that the sendall method on the socket is called when sending a message."""
        self.slipsocket.send_msg(b'hallo')
        self.slipsocket.send_msg(b'bye')
        self.sock_mock.sendall.assert_has_calls([
            mocker.call(END + b'hallo' + END),
            mocker.call(END + b'bye' + END)
        ])

    def test_receiving_data(self, mocker):
        """Test that the recv method on the socket is called when receiving a message.

        Also test that fragmented packets are buffered appropriately."""
        def socket_data_generator():
            yield END + b'hallo'
            yield END + END
            yield b'bye'
            yield END + END
            yield b''

        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        assert self.slipsocket.recv_msg() == b'hallo'
        # noinspection PyProtectedMember
        chunk_size = sliplib.SlipSocket._chunk_size  # pylint: disable=protected-access
        expected_calls = [mocker.call.recv(chunk_size)] * 2
        self.sock_mock.recv.assert_has_calls(expected_calls)
        assert self.slipsocket.recv_msg() == b'bye'
        expected_calls = [mocker.call.recv(chunk_size)] * 4
        self.sock_mock.recv.assert_has_calls(expected_calls)
        assert self.slipsocket.recv_msg() == b''
        expected_calls = [mocker.call.recv(chunk_size)] * 5
        self.sock_mock.recv.assert_has_calls(expected_calls)

    def test_end_of_data_handling(self, mocker):
        """Test that receipt of an empty byte string indicates the end of the connection."""
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
        chunk_size = sliplib.SlipSocket._chunk_size  # pylint: disable=protected-access
        expected_calls = [mocker.call.recv(chunk_size)] * 4
        self.sock_mock.recv.assert_has_calls(expected_calls)

    def test_exception_on_protocol_error_in_first_packet(self, mocker):
        """Test that an invalid packet causes a ProtocolError.

        Packets after the invalid packet are handled correctly."""
        def socket_data_generator():
            yield END + ESC + b'error' + END + b'hallo' + END + b'bye' + END

        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b'error',)
        assert self.slipsocket.recv_msg() == b'hallo'
        assert self.slipsocket.recv_msg() == b'bye'

    def test_exception_on_protocol_error_in_subsequent_packet(self, mocker):
        """Test that an invalid packet causes a ProtocolError

        Packets before the invalid packet are decoded correctly."""
        def socket_data_generator():
            yield END + b'hallo' + END + ESC + b'error' + END

        self.sock_mock.recv = mocker.Mock(side_effect=socket_data_generator())
        assert self.slipsocket.recv_msg() == b'hallo'
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b'error',)

    def test_exceptions_on_consecutive_invalid_packets(self, mocker):
        """Test that multiple invalid packets result in a ProtocolError for each invalid packet."""
        def socket_data_generator():
            yield END + b'hallo' + END + ESC + b'error' + END + b'another' + ESC + END + b'bye' + END

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
        """Test that the accept method is delegated to the socket, and that the result is a SlipSocket."""
        new_socket = mocker.Mock(spec=socket.socket(family=self.family), family=self.family,
                                 type=socket.SOCK_STREAM, proto=0)  # pylint: disable=no-member
        self.sock_mock.accept = mocker.Mock(return_value=(new_socket, self.far_address))
        new_slip_socket, address = self.slipsocket.accept()
        self.sock_mock.accept.assert_called_once_with()
        assert isinstance(new_slip_socket, SlipSocket)
        assert new_slip_socket.socket is new_socket
        assert address == self.far_address

    def test_bind_method(self, mocker):
        """Test that the bind method is delegated to the socket."""
        self.sock_mock.bind = mocker.Mock()
        self.slipsocket.bind(self.near_address)
        self.sock_mock.bind.assert_called_once_with(self.near_address)

    def test_close_method(self, mocker):
        """Test that the close method is delegated to the socket."""
        self.sock_mock.close = mocker.Mock()
        self.slipsocket.close()
        self.sock_mock.close.assert_called_once_with()

    def test_connect_method(self, mocker):
        """Test that the connect method is delegated to the socket."""
        self.sock_mock.connect = mocker.Mock()
        self.slipsocket.connect(self.far_address)
        self.sock_mock.connect.assert_called_once_with(self.far_address)

    def test_connect_ex_method(self, mocker):
        """Test that the connect_ex method is delegated to the socket."""
        self.sock_mock.connect_ex = mocker.Mock()
        self.slipsocket.connect_ex(self.far_address)
        self.sock_mock.connect_ex.assert_called_once_with(self.far_address)

    def test_getpeername_method(self, mocker):
        """Test that the getpeername method is delegated to the socket."""
        self.sock_mock.getpeername = mocker.Mock(return_value=self.far_address)
        peername = self.slipsocket.getpeername()
        self.sock_mock.getpeername.assert_called_once_with()
        assert peername == self.far_address

    def test_getsockname_method(self, mocker):
        """Test that the getsockname method is delegated to the socket."""
        self.sock_mock.getsockname = mocker.Mock(return_value=self.near_address)
        sockname = self.slipsocket.getsockname()
        self.sock_mock.getsockname.assert_called_once_with()
        assert sockname == self.near_address

    def test_listen_method(self, mocker):
        """Test that the listen method (with or without arguments) is delegated to the socket."""
        self.sock_mock.listen = mocker.Mock()
        self.slipsocket.listen()
        self.slipsocket.listen(5)
        assert self.sock_mock.listen.mock_calls == [mocker.call(), mocker.call(5)]

    def test_shutdown_method(self, mocker):
        """Test that the shutdown method is delegated to the socket."""
        self.sock_mock.shutdown = mocker.Mock()
        self.slipsocket.shutdown(0)
        self.sock_mock.shutdown.assert_called_once_with(0)

    @pytest.mark.parametrize('method', NOT_DELEGATED_METHODS)
    def test_exception_for_not_supported_operations(self, method):
        """Test that non-delegated methods on the SlipSocket raise an AttributeError."""
        with pytest.raises(AttributeError):
            getattr(self.slipsocket, method)

    # Testing delegated methods.
    # This will be removed due to deprecation of delegating methods to the wrapped socket.
    @pytest.mark.parametrize('method', DELEGATED_METHODS)
    def test_delegated_methods(self, method, mocker):
        """Test that other delegated methods are delegated to the socket, but also issue a deprecation warning."""
        mock_method = mocker.Mock()
        setattr(self.sock_mock, method, mock_method)
        with warnings.catch_warnings(record=True) as warning:
            socket_method = getattr(self.slipsocket, method)
            assert len(warning) == 1
            assert issubclass(warning[0].category, DeprecationWarning)
            assert "will be removed in version 1.0" in str(warning[0].message)
        socket_method()
        mock_method.assert_called_once_with()

    @pytest.mark.parametrize('attr', [
        'family', 'type', 'proto'
    ])
    def test_read_only_attribute(self, attr):
        """Test that read-only attributes can be read but not written."""
        assert getattr(self.slipsocket, attr) == getattr(self.slipsocket.socket, attr)
        with pytest.raises(AttributeError):
            setattr(self.slipsocket, attr, "some value")

    def test_create_connection(self, mocker):
        """Test that create_connection gives a SlipSocket."""
        new_sock_mock = mocker.Mock(spec=socket.socket(self.family), family=self.family,
                                    type=socket.SOCK_STREAM, proto=0)  # pylint: disable=no-member
        create_connection_mock = mocker.patch('sliplib.socket.create_connection', return_value=new_sock_mock)
        sock = SlipSocket.create_connection(self.far_address)
        assert isinstance(sock, SlipSocket)
        assert sock.socket is new_sock_mock
        create_connection_mock.assert_called_once_with(self.far_address[0:2], None, None)

    def test_slip_socket_iteration(self, mocker):
        """Test that a SlipSocket can be iterated over."""
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
