from typing import Generator

import pytest

from sliplib import END, config
from sliplib.legacy import decode, encode
from tests.unit.test_slip import message_packet


@pytest.mark.parametrize(
    ("message", "packet"),
    message_packet,
)
class TestLegacy:
    @pytest.fixture(autouse=True)
    def setup(self, *, send_leading_end_byte: bool) -> Generator[None, None, None]:
        """Test preparation."""
        previous_setting = config.USE_LEADING_END_BYTE
        config.USE_LEADING_END_BYTE = send_leading_end_byte
        self.prefix = END if send_leading_end_byte else b""
        yield
        config.USE_LEADING_END_BYTE = previous_setting

    def test_legacy_encode(self, message: bytes, packet: bytes) -> None:
        assert encode(message) == self.prefix + packet + END

    def test_legacy_decode(self, message: bytes, packet: bytes) -> None:
        assert decode(self.prefix + packet + END) == message
