# Copyright (c) 2024 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.


"""Tests for SlipSocket"""

from __future__ import annotations

import socket
import warnings
from typing import TYPE_CHECKING, Any, Generator

import pytest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from sliplib.slipsocket import TCPAddress

import sliplib
from sliplib import END, ESC, ProtocolError, SlipSocket, use_leading_end_byte

SOCKET_METHODS = [
    attr for attr in dir(socket.socket) if callable(getattr(socket.socket, attr)) and not attr.startswith("_")
]

EXPLICITLY_EXPOSED_SOCKET_METHODS = (
    "accept",
    "bind",
    "close",
    "connect",
    "connect_ex",
    "fileno",
    "getpeername",
    "getsockname",
    "getsockopt",
    "gettimeout",
    "listen",
    "setsockopt",
    "shutdown",
)

DELEGATED_METHODS = tuple(
    attr
    for attr in SOCKET_METHODS
    if not (
        attr.startswith(("recv", "send"))
        or attr in ("dup", "makefile", "share")
        or attr in EXPLICITLY_EXPOSED_SOCKET_METHODS
    )
)

NOT_DELEGATED_METHODS = tuple(
    attr for attr in SOCKET_METHODS if attr not in DELEGATED_METHODS and attr not in EXPLICITLY_EXPOSED_SOCKET_METHODS
)


@pytest.mark.parametrize(
    ("address", "family", "remote_address"),
    (
        (("127.0.0.1", 12345), socket.AF_INET, ("93.184.216.34", 54321)),
        (("::1", 12345, 0, 0), socket.AF_INET6, ("2606:2800:220:1:248:1893:25c8:1946", 54321, 0, 0)),
    ),
)
class TestSlipSocket:
    """Tests for SlipSocket"""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        address: TCPAddress,
        family: int,
        remote_address: TCPAddress,
        mocker: MockerFixture,
        *,
        send_leading_end_byte: bool,
    ) -> Generator[None, None, None]:
        """Prepare the test."""
        self.near_address = address
        self.family = family
        self.far_address = remote_address
        self.sock_mock = mocker.create_autospec(
            spec=socket.socket,
            instance=True,
            family=self.family,
            type=socket.SOCK_STREAM,
            proto=0,
        )
        with use_leading_end_byte(send_leading_end_byte):
            self.slipsocket = SlipSocket(self.sock_mock)
        yield
        self.sock_mock.close()
        del self.slipsocket

    def test_slipsocket_instantiation(self) -> None:
        """Test that the slipsocket has been created properly."""
        assert self.slipsocket.family == self.family
        assert self.slipsocket.type == socket.SOCK_STREAM
        assert self.slipsocket.proto == 0
        assert self.slipsocket.socket is self.sock_mock

    def test_slipsocket_requires_tcp_socket(self) -> None:
        """Test that non-TCP sockets are rejected."""
        self.sock_mock.configure_mock(type=socket.SOCK_DGRAM)
        with pytest.raises(ValueError, match="type SOCK_STREAM"):
            SlipSocket(self.sock_mock)

    def test_sending_data(self, mocker: MockerFixture, *, send_leading_end_byte: bool) -> None:
        """Test that the sendall method on the socket is called when sending a message."""
        prefix = END if send_leading_end_byte else b""
        self.slipsocket.send_msg(b"hallo")
        self.slipsocket.send_msg(b"bye")
        self.sock_mock.sendall.assert_has_calls(
            [mocker.call(prefix + b"hallo" + END), mocker.call(prefix + b"bye" + END)]
        )

    def test_receiving_data(self, mocker: MockerFixture) -> None:
        """Test that the recv method on the socket is called when receiving a message.

        Also test that fragmented packets are buffered appropriately."""

        def socket_data_generator() -> Generator[bytes, None, None]:
            yield END + b"hallo"
            yield END + END
            yield b"bye"
            yield END + END
            yield b""

        self.sock_mock.recv.side_effect = socket_data_generator()
        assert self.slipsocket.recv_msg() == b"hallo"
        chunk_size = sliplib.SlipSocket._chunk_size  # noqa: SLF001
        expected_calls = [mocker.call(chunk_size)] * 2
        self.sock_mock.recv.assert_has_calls(expected_calls)
        assert self.slipsocket.recv_msg() == b"bye"
        expected_calls = [mocker.call(chunk_size)] * 4
        self.sock_mock.recv.assert_has_calls(expected_calls)
        assert self.slipsocket.recv_msg() == b""
        expected_calls = [mocker.call(chunk_size)] * 5
        self.sock_mock.recv.assert_has_calls(expected_calls)

    def test_end_of_data_handling(self, mocker: MockerFixture) -> None:
        """Test that receipt of an empty byte string indicates the end of the connection."""

        def socket_data_generator() -> Generator[bytes, None, None]:
            yield END + b"hallo"
            yield END + END
            yield b"bye"
            yield b""
            yield b""  # no cov.  Extra byte to ensure that the previous empty byte is enough to signal end of data.

        self.sock_mock.recv.side_effect = socket_data_generator()
        assert self.slipsocket.recv_msg() == b"hallo"
        assert self.slipsocket.recv_msg() == b"bye"
        assert self.slipsocket.recv_msg() == b""
        chunk_size = sliplib.SlipSocket._chunk_size  # noqa: SLF001
        expected_calls = [mocker.call(chunk_size)] * 4
        self.sock_mock.recv.assert_has_calls(expected_calls)

    def test_exception_on_protocol_error_in_first_packet(self) -> None:
        """Test that an invalid packet causes a ProtocolError.

        Packets after the invalid packet are handled correctly."""

        def socket_data_generator() -> Generator[bytes, None, None]:
            yield END + ESC + b"error" + END + b"hallo" + END + b"bye" + END

        self.sock_mock.recv.side_effect = socket_data_generator()
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b"error",)
        assert self.slipsocket.recv_msg() == b"hallo"
        assert self.slipsocket.recv_msg() == b"bye"

    def test_exception_on_protocol_error_in_subsequent_packet(self) -> None:
        """Test that an invalid packet causes a ProtocolError

        Packets before the invalid packet are decoded correctly."""

        def socket_data_generator() -> Generator[bytes, None, None]:
            yield END + b"hallo" + END + ESC + b"error" + END

        self.sock_mock.recv.side_effect = socket_data_generator()
        assert self.slipsocket.recv_msg() == b"hallo"
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b"error",)

    def test_exceptions_on_consecutive_invalid_packets(
        self,
    ) -> None:
        """Test that multiple invalid packets result in a ProtocolError for each invalid packet."""

        def socket_data_generator() -> Generator[bytes, None, None]:
            yield END + b"hallo" + END + ESC + b"error" + END + b"another" + ESC + END + b"bye" + END

        self.sock_mock.recv.side_effect = socket_data_generator()
        assert self.slipsocket.recv_msg() == b"hallo"
        with pytest.raises(ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (ESC + b"error",)
        with pytest.raises(sliplib.ProtocolError) as exc:
            self.slipsocket.recv_msg()
        assert exc.value.args == (b"another" + ESC,)
        assert self.slipsocket.recv_msg() == b"bye"

    def test_accept_method(self, mocker: MockerFixture) -> None:
        """Test that the accept method is delegated to the socket, and that the result is a SlipSocket."""
        new_socket = mocker.create_autospec(
            spec=socket.socket,
            instance=True,
            family=self.family,
            type=socket.SOCK_STREAM,
            proto=0,
        )
        self.sock_mock.accept.return_value = (new_socket, self.far_address)
        new_slip_socket, address = self.slipsocket.accept()
        self.sock_mock.accept.assert_called_once_with()
        assert isinstance(new_slip_socket, SlipSocket)
        assert new_slip_socket.socket is new_socket
        assert address == self.far_address
        new_socket.close()

    def test_bind_method(self) -> None:
        """Test that the bind method is delegated to the socket."""
        self.slipsocket.bind(self.near_address)
        self.sock_mock.bind.assert_called_once_with(self.near_address)

    def test_close_method(self) -> None:
        """Test that the close method is delegated to the socket."""
        self.slipsocket.close()
        self.sock_mock.close.assert_called_once_with()

    def test_connect_method(self) -> None:
        """Test that the connect method is delegated to the socket."""
        self.slipsocket.connect(self.far_address)
        self.sock_mock.connect.assert_called_once_with(self.far_address)

    def test_connect_ex_method(self) -> None:
        """Test that the connect_ex method is delegated to the socket."""
        self.slipsocket.connect_ex(self.far_address)
        self.sock_mock.connect_ex.assert_called_once_with(self.far_address)

    def test_fileno_method(self) -> None:
        """Test that the fileno method is delegated to the socket."""
        self.sock_mock.fileno.return_value = 3
        fileno = self.slipsocket.fileno()
        self.sock_mock.fileno.assert_called_once_with()
        assert fileno == 3

    def test_getpeername_method(self) -> None:
        """Test that the getpeername method is delegated to the socket."""
        self.sock_mock.getpeername.return_value = self.far_address
        peername = self.slipsocket.getpeername()
        self.sock_mock.getpeername.assert_called_once_with()
        assert peername == self.far_address

    def test_getsockname_method(self) -> None:
        """Test that the getsockname method is delegated to the socket."""
        self.sock_mock.getsockname.return_value = self.near_address
        sockname = self.slipsocket.getsockname()
        self.sock_mock.getsockname.assert_called_once_with()
        assert sockname == self.near_address

    def test_getsockopt_method(self) -> None:
        """Test that the getsockopt method is delegated to the socket."""
        self.sock_mock.getsockopt.return_value = 5
        option = self.slipsocket.getsockopt(27, 5)
        self.sock_mock.getsockopt.assert_called_once_with(27, 5)
        assert option == 5

    def test_listen_method(self, mocker: MockerFixture) -> None:
        """Test that the listen method (with or without arguments) is delegated to the socket."""
        self.slipsocket.listen()
        self.slipsocket.listen(5)
        assert self.sock_mock.listen.mock_calls == [mocker.call(), mocker.call(5)]

    def test_setsockopt_method(self) -> None:
        """Test that the getsockopt method is delegated to the socket."""
        self.slipsocket.setsockopt(27, 5)
        self.sock_mock.setsockopt.assert_called_once_with(27, 5)

    def test_shutdown_method(self) -> None:
        """Test that the shutdown method is delegated to the socket."""
        self.slipsocket.shutdown(0)
        self.sock_mock.shutdown.assert_called_once_with(0)

    @pytest.mark.parametrize("method", NOT_DELEGATED_METHODS)
    def test_exception_for_not_supported_operations(self, method: str) -> None:
        """Test that non-delegated methods on the SlipSocket raise an AttributeError."""
        with pytest.raises(AttributeError):
            getattr(self.slipsocket, method)

    # Testing delegated methods.
    # This will be removed due to deprecation of delegating methods to the wrapped socket.
    @pytest.mark.parametrize("method", DELEGATED_METHODS)
    def test_delegated_methods(self, method: str) -> None:
        """Test that other delegated methods are delegated to the socket, but also issue a deprecation warning."""
        with warnings.catch_warnings(record=True) as warning:
            socket_method = getattr(self.slipsocket, method)
            assert len(warning) == 1
            assert issubclass(warning[0].category, DeprecationWarning)
            assert "will be removed in version 1.0" in str(warning[0].message)
        if method == "set_inheritable":
            args: tuple[()] | tuple[Any] = (True,)
        else:
            args = ()
        socket_method(*args)
        getattr(self.sock_mock, method).assert_called_once_with(*args)

    @pytest.mark.parametrize("attr", ["family", "type", "proto"])
    def test_read_only_attribute(self, attr: str) -> None:
        """Test that read-only attributes can be read but not written."""
        assert getattr(self.slipsocket, attr) == getattr(self.slipsocket.socket, attr)
        with pytest.raises(AttributeError):
            setattr(self.slipsocket, attr, "some value")

    def test_create_connection(self, mocker: MockerFixture) -> None:
        """Test that create_connection gives a SlipSocket."""
        new_sock_mock = mocker.create_autospec(
            spec=socket.socket,
            instance=True,
            family=self.family,
            type=socket.SOCK_STREAM,
            proto=0,
        )
        create_connection_mock = mocker.patch("sliplib.slipsocket.socket.create_connection", return_value=new_sock_mock)
        sock = SlipSocket.create_connection(self.far_address)
        assert isinstance(sock, SlipSocket)
        assert sock.socket is new_sock_mock
        create_connection_mock.assert_called_once_with(self.far_address[0:2], None, None)
        sock.close()
        new_sock_mock.close()

    def test_slip_socket_iteration(self) -> None:
        """Test that a SlipSocket can be iterated over."""

        def socket_data_generator() -> Generator[bytes, None, None]:
            yield END + b"hallo"
            yield END + END
            yield b"bye"
            yield END + END
            yield b""

        self.sock_mock.recv.side_effect = socket_data_generator()
        expected = (b"hallo", b"bye")
        actual = tuple(msg for msg in self.slipsocket)
        assert expected == actual
