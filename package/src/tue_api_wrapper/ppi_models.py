from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PpiLecture:
    id: int | None
    title: str
    protocol_count: int
    borrowed: bool
    can_borrow: bool


@dataclass(slots=True)
class PpiLectureCatalog:
    tokens: int
    source_url: str
    lectures: list[PpiLecture] = field(default_factory=list)


@dataclass(slots=True)
class PpiBorrowedLecture:
    id: int | None
    title: str
    borrowed_until: str
    download_available: bool


@dataclass(slots=True)
class PpiBorrowedLecturesPage:
    tokens: int
    source_url: str
    lectures: list[PpiBorrowedLecture] = field(default_factory=list)


@dataclass(slots=True)
class PpiSignupResult:
    username: str
    activation_email: str
    activation_required: bool = True


@dataclass(slots=True)
class PpiDownload:
    lecture_id: int
    filename: str
    content_type: str
    data: bytes


@dataclass(slots=True)
class PpiTokenRequestResult:
    submitted: bool
