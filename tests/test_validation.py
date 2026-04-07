"""Tests for input validation and security controls."""

import pytest

from steam_blade_mcp.validation import (
    validate_app_id,
    validate_count,
    validate_ip_address,
    validate_steam_id,
    validate_vanity_url,
)


class TestSteamIdValidation:
    def test_valid_steam_id(self):
        assert validate_steam_id("76561198012345678") == "76561198012345678"

    def test_too_short(self):
        with pytest.raises(ValueError, match="exactly 17 digits"):
            validate_steam_id("7656119801234")

    def test_too_long(self):
        with pytest.raises(ValueError, match="exactly 17 digits"):
            validate_steam_id("765611980123456789")

    def test_non_numeric(self):
        with pytest.raises(ValueError, match="exactly 17 digits"):
            validate_steam_id("7656119801234567a")

    def test_empty(self):
        with pytest.raises(ValueError, match="exactly 17 digits"):
            validate_steam_id("")

    def test_masks_value_in_error(self):
        with pytest.raises(ValueError, match=r"\*\*\*"):
            validate_steam_id("not-a-steam-id-at-all")


class TestVanityUrlValidation:
    def test_valid(self):
        assert validate_vanity_url("testplayer") == "testplayer"

    def test_valid_with_special(self):
        assert validate_vanity_url("test_player-123") == "test_player-123"

    def test_too_long(self):
        with pytest.raises(ValueError, match="1-32 chars"):
            validate_vanity_url("a" * 33)

    def test_invalid_chars(self):
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_vanity_url("test player")

    def test_empty(self):
        with pytest.raises(ValueError):
            validate_vanity_url("")


class TestAppIdValidation:
    def test_valid(self):
        assert validate_app_id(730) == 730

    def test_zero(self):
        with pytest.raises(ValueError, match="must be 1"):
            validate_app_id(0)

    def test_negative(self):
        with pytest.raises(ValueError, match="must be 1"):
            validate_app_id(-1)

    def test_too_large(self):
        with pytest.raises(ValueError, match="must be 1"):
            validate_app_id(100_000_000)


class TestIpValidation:
    def test_valid_public(self):
        assert validate_ip_address("8.8.8.8") == "8.8.8.8"

    def test_blocks_private_10(self):
        with pytest.raises(ValueError, match="Private"):
            validate_ip_address("10.0.0.1")

    def test_blocks_private_172(self):
        with pytest.raises(ValueError, match="Private"):
            validate_ip_address("172.16.0.1")

    def test_blocks_private_192(self):
        with pytest.raises(ValueError, match="Private"):
            validate_ip_address("192.168.1.1")

    def test_blocks_loopback(self):
        with pytest.raises(ValueError, match="Loopback"):
            validate_ip_address("127.0.0.1")

    def test_blocks_link_local(self):
        with pytest.raises(ValueError, match="Link-local"):
            validate_ip_address("169.254.0.1")

    def test_blocks_multicast(self):
        with pytest.raises(ValueError, match="Multicast"):
            validate_ip_address("224.0.0.1")

    def test_blocks_documentation_192_0_2(self):
        with pytest.raises(ValueError, match="Documentation"):
            validate_ip_address("192.0.2.1")

    def test_blocks_documentation_198_51_100(self):
        with pytest.raises(ValueError, match="Documentation"):
            validate_ip_address("198.51.100.1")

    def test_blocks_documentation_203_0_113(self):
        with pytest.raises(ValueError, match="Documentation"):
            validate_ip_address("203.0.113.1")

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid IP"):
            validate_ip_address("not-an-ip")


class TestCountValidation:
    def test_valid(self):
        assert validate_count(10, 100) == 10

    def test_min(self):
        assert validate_count(1, 100) == 1

    def test_max(self):
        assert validate_count(100, 100) == 100

    def test_zero(self):
        with pytest.raises(ValueError, match="at least 1"):
            validate_count(0, 100)

    def test_exceeds_max(self):
        with pytest.raises(ValueError, match="at most 100"):
            validate_count(101, 100)
