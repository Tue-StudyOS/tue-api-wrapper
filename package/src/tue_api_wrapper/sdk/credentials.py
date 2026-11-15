from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class UniversityCredentials:
    username: str
    password: str = field(repr=False)

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> "UniversityCredentials":
        values = read_env_file(env_file)
        username = _read_first(values, "UNI_USERNAME", "ALMA_USERNAME", "ILIAS_USERNAME")
        password = _read_first(values, "UNI_PASSWORD", "ALMA_PASSWORD", "ILIAS_PASSWORD")
        if not username or not password:
            raise ValueError(
                "Set UNI_USERNAME and UNI_PASSWORD in the environment, in .env, "
                "or pass credentials directly to TuebingenAuthenticatedClient.login(...)."
            )
        return cls(username=username, password=password)


def read_env_file(path: str | Path | None) -> dict[str, str]:
    if path is None:
        return {}
    env_path = Path(path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _clean_env_value(value)
    return values


def _read_first(values: dict[str, str], *names: str) -> str | None:
    for name in names:
        value = os.getenv(name) or values.get(name)
        if value:
            return value
    return None


def _clean_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
