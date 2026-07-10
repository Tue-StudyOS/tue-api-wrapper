from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlmaAccountProfile:
    current_role: str
    available_roles: tuple[str, ...]
