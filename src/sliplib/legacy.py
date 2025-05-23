#  Copyright (c) 2025. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
Module :mod:`~sliplib.legacy`
=============================

This module contains the legacy versions of the :func:`~sliplib.slip.encode()`
and :func:`~sliplib.slip.decode()` functions,
as they were defined prior to version 0.7.0.
Note that usage of these functions is discouraged.
When using these functions, the responsibility to properly split incoming data into SLIP packets,
and buffer incomplete SLIP packets resides completely with the user.

.. autofunction:: encode
.. autofunction:: decode

"""

import sliplib
from sliplib import END, config


def decode(packet: bytes) -> bytes:
    """Extract the original message from a SLIP packet.

    Args:
        packet: the SLIP packet to decode.

    Returns:
        The decoded message.

    Raises:
        ProtocolError: if the packet cannot be decoded.
    """
    return sliplib.decode(packet.strip(END))


def encode(message: bytes) -> bytes:
    """Encode a message into a SLIP packet.

    Note that the SLIP packet will start with a leading :const:`~config.END` byte if the current value
    of :data:`~sliplib.config.USE_LEADING_END_BYTE` is True. A leading :const:`~config.END` byte will be absent
    if the current value of :data:`~sliplib.config.USE_LEADING_END_BYTE` is False.

    Args:
        message: The message to encode.

    Returns:
        The encoded message.
    """
    return (END if config.USE_LEADING_END_BYTE else b"") + sliplib.encode(message) + END
