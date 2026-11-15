from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path

from .sdk import TuebingenAuthenticatedClient, UniversityCredentials


def make_client(env_file: str | Path | None):
    credentials = UniversityCredentials.from_env(env_file)
    return TuebingenAuthenticatedClient(credentials), credentials.username


def state_path(username: str) -> Path:
    root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    account = sha256(username.strip().casefold().encode()).hexdigest()
    return root / "tue-api-wrapper" / "study-radar" / f"{account}.json"
