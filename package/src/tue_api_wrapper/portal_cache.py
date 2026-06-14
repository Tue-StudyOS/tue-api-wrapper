from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from threading import RLock
import time
from typing import Callable, TypeVar

T = TypeVar("T")
CacheKey = tuple[object, ...]


@dataclass(frozen=True, slots=True)
class CacheConfig:
    enabled: bool = False
    ttl_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")


@dataclass(slots=True)
class _CacheEntry:
    expires_at: float
    value: object


class PortalCache:
    def __init__(
        self,
        config: CacheConfig | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._config = config or CacheConfig()
        self._clock = clock
        self._entries: dict[CacheKey, _CacheEntry] = {}
        self._lock = RLock()

    @property
    def config(self) -> CacheConfig:
        return self._config

    def configure(
        self,
        *,
        enabled: bool | None = None,
        ttl_seconds: float | None = None,
    ) -> CacheConfig:
        next_config = CacheConfig(
            enabled=self._config.enabled if enabled is None else enabled,
            ttl_seconds=self._config.ttl_seconds if ttl_seconds is None else ttl_seconds,
        )
        with self._lock:
            self._config = next_config
            if not next_config.enabled:
                self._entries.clear()
        return next_config

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def invalidate(self, *, prefix: CacheKey | None = None) -> None:
        with self._lock:
            if prefix is None:
                self._entries.clear()
                return
            for key in [existing for existing in self._entries if existing[: len(prefix)] == prefix]:
                self._entries.pop(key, None)

    def get_or_load(self, key: CacheKey, loader: Callable[[], T]) -> T:
        if not self._config.enabled:
            return loader()

        cached = self._get(key)
        if cached is not None:
            return cached

        value = loader()
        with self._lock:
            self._entries[key] = _CacheEntry(
                expires_at=self._clock() + self._config.ttl_seconds,
                value=value,
            )
        return value

    def _get(self, key: CacheKey) -> T | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= self._clock():
                self._entries.pop(key, None)
                return None
            return entry.value  # type: ignore[return-value]


_DEFAULT_PORTAL_CACHE = PortalCache()


def default_portal_cache() -> PortalCache:
    return _DEFAULT_PORTAL_CACHE


def configure_portal_cache(*, enabled: bool, ttl_seconds: float = 60.0) -> CacheConfig:
    return _DEFAULT_PORTAL_CACHE.configure(enabled=enabled, ttl_seconds=ttl_seconds)


def clear_portal_cache() -> None:
    _DEFAULT_PORTAL_CACHE.clear()


def credential_scope(namespace: str, *parts: str | None) -> str:
    payload = "\0".join(part or "" for part in parts)
    if not payload:
        return f"{namespace}:anonymous"
    digest = sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{namespace}:{digest}"
