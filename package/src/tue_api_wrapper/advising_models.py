from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdvisingLink:
    label: str
    url: str


@dataclass(frozen=True)
class AdvisingField:
    label: str
    value: str
    links: tuple[AdvisingLink, ...] = ()


@dataclass(frozen=True)
class AdvisingTopic:
    topic: str
    guidance: str
    links: tuple[AdvisingLink, ...] = ()


@dataclass(frozen=True)
class AdvisingPage:
    source_url: str
    title: str
    name: str | None
    contact: tuple[AdvisingField, ...]
    can_help: tuple[AdvisingTopic, ...]
    cannot_help: tuple[AdvisingTopic, ...]
