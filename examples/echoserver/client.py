# ruff: noqa: T201

# Copyright (c) 2020 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

"""
Client
++++++

The :file:`client.py` example file is a client for the demonstrator echo server.
It prompts the user for a message,
encodes it in a Slip packet, sends it to the server,
and prints the decoded reply it gets back from the server.
This is repeated until the user enters an empty message.
"""

# ruff: noqa: T201
import sys

import sliplib

if __name__ == "__main__":
    if len(sys.argv) != 2:  # noqa: PLR2004
        print("Usage: python client.py <port>")
        sys.exit(1)
    port = sys.argv[1]
    print(f"Connecting to server on port {port}")
    sock = sliplib.SlipSocket.create_connection(("localhost", int(port)))
    print(f"Connected to {sock.getpeername()}")

    while True:
        message = input("Message>")
        if not message:
            break
        b_message = bytes(message, "utf-8")
        sock.send_msg(b_message)
        b_reply = sock.recv_msg()
        print("Response:", b_reply)
