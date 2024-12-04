# Copyright (c) 2024 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

from importlib.metadata import version

from semantic_version_check import version_check


def test_version() -> None:
    __version__ = version("sliplib")
    assert version_check(__version__)
