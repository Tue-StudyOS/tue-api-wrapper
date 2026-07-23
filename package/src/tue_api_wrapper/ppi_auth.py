from __future__ import annotations

import os

from .ppi_client import PpiClient, PpiError


class PpiConfigurationError(PpiError):
    pass


def read_ppi_credentials() -> tuple[str | None, str | None]:
    return os.getenv("PPI_USERNAME"), os.getenv("PPI_PASSWORD")


def build_ppi_client() -> PpiClient:
    username, password = read_ppi_credentials()
    if not username or not password:
        raise PpiConfigurationError(
            "Set PPI_USERNAME and PPI_PASSWORD before using authenticated PPI endpoints. "
            "Use a PPI-specific password, not UNI_PASSWORD."
        )
    client = PpiClient()
    try:
        client.login(username, password)
    except Exception:
        client.close()
        raise
    return client
