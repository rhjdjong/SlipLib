import pytest

import sliplib
from sliplib import config, use_leading_end_byte


class TestConfigValues:
    def test_end_byte(self) -> None:
        assert config.END == b"\xc0"

    def test_esc_byte(self) -> None:
        assert config.ESC == b"\xdb"

    def test_esc_end_byte(self) -> None:
        assert config.ESC_END == b"\xdc"

    def test_esc_esc_byte(self) -> None:
        assert config.ESC_ESC == b"\xdd"

    def test_use_leading_end_byte(self) -> None:
        assert config.USE_LEADING_END_BYTE is False

    def test_modifying_use_leading_end_byte_setting(self) -> None:
        with config._use_leading_end_byte_lock:  # noqa: SLF001
            config.USE_LEADING_END_BYTE = True
            assert config.USE_LEADING_END_BYTE is True
            config.USE_LEADING_END_BYTE = False
            assert config.USE_LEADING_END_BYTE is False

    def test_export_from_top_level_module(self) -> None:
        assert sliplib.END == config.END
        assert sliplib.ESC == config.ESC
        assert sliplib.ESC_END == config.ESC_END
        assert sliplib.ESC_ESC == config.ESC_ESC
        assert sliplib.use_leading_end_byte.__func__ is config.use_leading_end_byte.__func__  # type: ignore[attr-defined]

    def test_modifying_slip_bytes_fails(self) -> None:
        with pytest.raises(AttributeError):
            config.END = b"oops"  # type: ignore[misc]
        with pytest.raises(AttributeError):
            config.ESC = b"oops"  # type: ignore[misc]
        with pytest.raises(AttributeError):
            config.ESC_END = b"oops"  # type: ignore[misc]
        with pytest.raises(AttributeError):
            config.ESC_ESC = b"oops"  # type: ignore[misc]


class TestUseLeadingEndByteContextManager:
    def test_use_leading_end_byte(self, *, send_leading_end_byte: bool) -> None:
        earlier_value = config.USE_LEADING_END_BYTE
        with use_leading_end_byte(send_leading_end_byte):
            temp_value = config.USE_LEADING_END_BYTE
        assert earlier_value == config.USE_LEADING_END_BYTE
        assert temp_value == send_leading_end_byte

    def test_nested_context_managers(self, *, send_leading_end_byte: bool) -> None:
        start_value = config.USE_LEADING_END_BYTE
        with use_leading_end_byte(send_leading_end_byte):
            intermediate_value = config.USE_LEADING_END_BYTE
            for value in (False, True):
                with use_leading_end_byte(value):
                    temporary_value = config.USE_LEADING_END_BYTE
                assert temporary_value == value
                assert send_leading_end_byte == config.USE_LEADING_END_BYTE
            assert intermediate_value == config.USE_LEADING_END_BYTE
        assert start_value == config.USE_LEADING_END_BYTE
