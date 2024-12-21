#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.


"""
This module tests SlipSocket using a SLIP echo server, similar to the one in the examples directory.
"""

from __future__ import annotations

import pathlib
import re
import sys
import threading
from queue import Empty, Queue
from subprocess import PIPE, Popen
from typing import Generator

import pytest

import sliplib

END = sliplib.END


class TestEchoServer:
    def output_reader(self, proc: Popen[str], output_queue: Queue[str]) -> None:
        for line in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
            output_queue.put(line)

    def get_server_output(self) -> str:
        try:
            output: str = self.server_queue.get(timeout=10)
        except Empty:  # no cov
            pytest.fail("No output from server")
        return output.strip()

    def get_client_output(self) -> str:
        try:
            output: str = self.client_queue.get(timeout=10)
        except Empty:  # no cov
            pytest.fail("No output from client")
        return output.strip()

    def write_client_input(self, msg: str) -> None:
        self.client.stdin.write(msg + "\n")  # type: ignore[union-attr]
        self.client.stdin.flush()  # type: ignore[union-attr]

    @pytest.fixture(autouse=True)
    def setup(self) -> Generator[None, None, None]:
        echoserver_directory = pathlib.Path(sliplib.__file__).parents[2] / "examples" / "echoserver"
        self.python = pathlib.Path(sys.executable)
        self.server_script = str(echoserver_directory / "server.py")
        self.client_script = str(echoserver_directory / "client.py")
        self.server: Popen[str] | None = None
        self.client: Popen[str] | None = None
        self.server_queue: Queue[str] = Queue()
        self.client_queue: Queue[str] = Queue()
        yield
        if self.server and self.server.returncode is None:  # no cov
            self.server.terminate()
        if self.client and self.client.returncode is None:  # no cov
            self.client.terminate()

    @pytest.mark.parametrize("arg", ["", "ipv6"])
    def test_server_and_client(self, arg: str, *, send_leading_end_byte: bool, receive_leading_end_byte: bool) -> None:
        end_str = repr(END)[2:-1]
        server_prefix: str = end_str if send_leading_end_byte else ""
        client_prefix: str = end_str if receive_leading_end_byte else ""
        server_command = [
            "python",
            "-u",
            "-c",
            (
                "from sys import argv\n"
                "from pathlib import Path\n"
                "from sliplib import use_leading_end_byte\n"
                f"if '{arg}':\n"
                f"    argv.append('{arg}')\n"
                f"with use_leading_end_byte({send_leading_end_byte}):\n"
                f"    exec(Path('{self.server_script}').read_text())"
            ),
        ]
        self.server = Popen(
            server_command, executable=self.python, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, bufsize=1
        )
        server_output_reader = threading.Thread(target=self.output_reader, args=(self.server, self.server_queue))
        server_output_reader.start()
        server_output = self.get_server_output()
        m = re.match(r"Slip server listening on localhost, port (\d+)", server_output)
        assert m is not None
        server_port = m.group(1)

        client_command = [
            "python",
            "-u",
            "-c",
            (
                "from sys import argv\n"
                "from pathlib import Path\n"
                "from sliplib import use_leading_end_byte\n"
                f"argv.append({server_port})\n"
                f"with use_leading_end_byte({receive_leading_end_byte}):\n"
                f"    exec(Path('{self.client_script}').read_text())"
            ),
        ]
        self.client = Popen(
            client_command, executable=self.python, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, bufsize=1
        )
        client_output_reader = threading.Thread(target=self.output_reader, args=(self.client, self.client_queue))
        client_output_reader.start()
        client_output = self.get_client_output()
        assert client_output == f"Connecting to server on port {server_port}"

        server_output = self.get_server_output()
        message = f"Incoming connection from ('{'::1' if arg else '127.0.0.1'}'"
        assert server_output.startswith(message)

        client_output = self.get_client_output()
        message = f"Connected to ('{'::1' if arg else '127.0.0.1'}'"
        assert client_output.startswith(message)

        self.write_client_input("hallo")
        server_output = self.get_server_output()
        assert server_output == rf"Raw data received: b'{client_prefix}hallo{end_str}'"
        server_output = self.get_server_output()
        assert server_output == "Decoded data: b'hallo'"
        server_output = self.get_server_output()
        assert server_output == rf"Sending raw data: b'{server_prefix}ollah{end_str}'"
        client_output = self.get_client_output()
        assert client_output == "Message>Response: b'ollah'"

        self.write_client_input("bye")
        server_output = self.get_server_output()
        assert server_output == rf"Raw data received: b'{client_prefix}bye{end_str}'"
        server_output = self.get_server_output()
        assert server_output == "Decoded data: b'bye'"
        server_output = self.get_server_output()
        assert server_output == rf"Sending raw data: b'{server_prefix}eyb{end_str}'"
        client_output = self.get_client_output()
        assert client_output == "Message>Response: b'eyb'"

        self.write_client_input("")
        server_output = self.get_server_output()
        assert server_output == "Raw data received: b''"
        server_output = self.get_server_output()
        assert server_output == "Decoded data: b''"
        server_output = self.get_server_output()
        assert server_output == "Closing down"
        client_output = self.get_client_output()
        assert client_output == "Message>"

        assert self.server_queue.empty()
        assert self.client_queue.empty()
        self.server.wait(2)
        self.client.wait(2)
        assert self.server.returncode == 0
        assert self.client.returncode == 0
