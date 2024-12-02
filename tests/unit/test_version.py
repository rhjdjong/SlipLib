# Copyright (c) 2024 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

from semantic_version_check import version_check

from sliplib import version

assert version_check(version.__version__)
