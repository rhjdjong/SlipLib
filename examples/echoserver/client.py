# ruff: noqa: T201, EXE002

# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

"""
Client
++++++

The :file:`client.py` example file is a client for the demonstrator echo server.

Usage:
  python client.py <port> [ipv6]

The user must provide the port on which the echo server is listening.
The optional third argument indicates if an IPv6 connection must be used
(default is IPv4).

The script prompts the user for a message,
encodes it in a Slip packet, sends it to the server,
and prints the decoded reply it gets back from the server.
This is repeated until the user enters an empty message.
"""

import sys

import sliplib


def main() -> None:
    if not 1 < len(sys.argv) < 4:  # noqa: PLR2004
        print("Usage: python client.py <port> [ipv6]")
        sys.exit(1)
    port = sys.argv[1]

    # Avoid terms like "localhost" or "ipv6-localhost",
    # as the resolution of these terms are dependent on the system
    # and on the contents of /etc/hosts on Linux
    host = "::1" if len(sys.argv) == 3 else "127.0.0.1"  # noqa: PLR2004

    print(f"Connecting to server at {host}:{port}")
    sock = sliplib.SlipSocket.create_connection((host, int(port)))
    print(f"Connected to {sock.getpeername()}")

    while True:
        message = input("Message>")
        if not message:
            break
        b_message = bytes(message, "utf-8")
        sock.send_msg(b_message)
        b_reply = sock.recv_msg()
        print("Response:", b_reply)


if __name__ == "__main__":
    main()
