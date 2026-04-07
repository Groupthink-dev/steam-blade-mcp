"""Input validation and security controls."""

import ipaddress
import re

STEAM_ID_RE = re.compile(r"^[0-9]{17}$")
VANITY_URL_RE = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")
APP_ID_MAX = 10_000_000


def validate_steam_id(steam_id: str) -> str:
    """Validate a 64-bit Steam ID (17 digits)."""
    if not STEAM_ID_RE.match(steam_id):
        raise ValueError(
            f"Invalid Steam ID: must be exactly 17 digits. Got: {_mask(steam_id)}"
        )
    return steam_id


def validate_vanity_url(vanity: str) -> str:
    """Validate a Steam vanity URL slug."""
    if not VANITY_URL_RE.match(vanity):
        raise ValueError(
            "Invalid vanity URL: alphanumeric, underscores, hyphens, "
            f"1-32 chars. Got: {_mask(vanity)}"
        )
    return vanity


def validate_app_id(app_id: int) -> int:
    """Validate a Steam app ID is within reasonable bounds."""
    if not (0 < app_id <= APP_ID_MAX):
        raise ValueError(f"Invalid app ID: must be 1-{APP_ID_MAX}. Got: {app_id}")
    return app_id


def validate_ip_address(ip: str) -> str:
    """Validate an IP address is not in a private/reserved range (SSRF protection)."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        raise ValueError(f"Invalid IP address: {ip}") from None

    # Check specific categories before the broad is_private
    # (Python 3.11+ is_private includes loopback, link-local, and doc ranges)
    if addr.is_loopback:
        raise ValueError("Loopback addresses are not allowed (SSRF protection)")
    if addr.is_link_local:
        raise ValueError("Link-local addresses are not allowed (SSRF protection)")
    if addr.is_multicast:
        raise ValueError("Multicast addresses are not allowed (SSRF protection)")

    # Block documentation ranges explicitly
    doc_ranges = [
        ipaddress.ip_network("192.0.2.0/24"),
        ipaddress.ip_network("198.51.100.0/24"),
        ipaddress.ip_network("203.0.113.0/24"),
    ]
    for net in doc_ranges:
        if addr in net:
            raise ValueError("Documentation-range addresses are not allowed (SSRF protection)")

    if addr.is_reserved:
        raise ValueError("Reserved addresses are not allowed (SSRF protection)")
    if addr.is_private:
        raise ValueError("Private IP addresses are not allowed (SSRF protection)")

    return ip


def validate_count(count: int, max_val: int, label: str = "count") -> int:
    """Validate a count parameter is within bounds."""
    if count < 1:
        raise ValueError(f"{label} must be at least 1")
    if count > max_val:
        raise ValueError(f"{label} must be at most {max_val}")
    return count


def _mask(value: str) -> str:
    """Mask a value for safe error display."""
    if len(value) <= 4:
        return "***"
    return value[:2] + "***" + value[-2:]
