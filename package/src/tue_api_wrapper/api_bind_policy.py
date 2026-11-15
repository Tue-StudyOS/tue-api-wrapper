from __future__ import annotations

from ipaddress import ip_address

from .credentials import read_uni_credentials


def validate_api_bind_host(host: str) -> None:
    """Prevent accidental network exposure of the environment-backed account."""
    username, password = read_uni_credentials()
    if not username and not password:
        return

    if host == "localhost":
        return
    try:
        if ip_address(host).is_loopback:
            return
    except ValueError:
        pass

    raise ValueError(
        "The API server cannot bind to a non-loopback host while university "
        "credentials are configured. Use HOST=127.0.0.1 or HOST=::1 for local "
        "authenticated use. For public-data hosting, remove UNI_*, ALMA_*, "
        "and ILIAS_* login credentials from the server environment."
    )
