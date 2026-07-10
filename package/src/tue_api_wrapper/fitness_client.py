from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image

from .config import DEFAULT_TIMEOUT_SECONDS
from .fitness_models import KufOccupancyPage, KufTrainingOccupancy

KUF_OCCUPANCY_PAGE_URL = (
    "https://buchung.hsp.uni-tuebingen.de/angebote/aktueller_zeitraum/"
    "_Anzahl_der_Trainierenden_in_der_KuF.html"
)
KUF_FACILITY_ID = "kuf"


@dataclass(slots=True)
class _DigitFeatures:
    holes: int
    aspect: float
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    g: float
    tr: float
    bl: float


def parse_kuf_occupancy_page(html: str, page_url: str) -> KufOccupancyPage:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one(".bs_head")
    image_node = soup.select_one('img[src*="studio.cgi"]') or soup.find("img", alt=lambda value: value and "Auslastung" in value)
    if image_node is None:
        raise ValueError("KuF occupancy page did not expose the studio count image.")

    title = title_node.get_text(" ", strip=True) if title_node is not None else "Anzahl der Trainierenden in der KuF"
    raw_image_url = image_node.get("src", "").strip()
    if not raw_image_url:
        raise ValueError("KuF occupancy image URL was empty.")
    return KufOccupancyPage(facility_name=title, source_url=page_url, image_url=urljoin(page_url, raw_image_url))


def parse_kuf_training_count_image(image_bytes: bytes) -> int:
    try:
        source_image = Image.open(BytesIO(image_bytes))
    except Exception as error:  # pragma: no cover - Pillow error shape is version-specific
        raise ValueError("KuF occupancy image could not be decoded.") from error

    with source_image:
        if source_image.width > 400 or source_image.height > 200:
            raise ValueError("KuF occupancy image was larger than expected.")
        try:
            image = source_image.convert("RGBA")
        except Exception as error:  # pragma: no cover - Pillow error shape is version-specific
            raise ValueError("KuF occupancy image could not be decoded.") from error

    mask = _black_pixel_mask(image)
    digit_bounds = _digit_bounds(mask)
    if not digit_bounds:
        raise ValueError("KuF occupancy image did not contain readable digits.")

    digits = [_classify_digit(_features_for_digit(_crop_mask(mask, bounds))) for bounds in digit_bounds]
    return int("".join(digits))


class FitnessClient:
    def __init__(self, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.timeout = timeout

    def fetch_kuf_training_occupancy(self) -> KufTrainingOccupancy:
        page_response = requests.get(KUF_OCCUPANCY_PAGE_URL, timeout=self.timeout)
        page_response.raise_for_status()
        page = parse_kuf_occupancy_page(page_response.text, page_response.url)

        image_response = requests.get(page.image_url, timeout=self.timeout)
        image_response.raise_for_status()
        count = parse_kuf_training_count_image(image_response.content)

        return KufTrainingOccupancy(
            facility_id=KUF_FACILITY_ID,
            facility_name=page.facility_name,
            count=count,
            source_url=page.source_url,
            image_url=page.image_url,
            retrieved_at=datetime.now(timezone.utc),
            refresh_after_seconds=900,
        )


def _black_pixel_mask(image: Image.Image) -> list[list[bool]]:
    width, height = image.size
    mask: list[list[bool]] = []
    for y in range(height):
        row: list[bool] = []
        for x in range(width):
            red, green, blue, alpha = image.getpixel((x, y))
            row.append(alpha > 0 and red + green + blue < 540)
        mask.append(row)
    return mask


def _digit_bounds(mask: list[list[bool]]) -> list[tuple[int, int, int, int]]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    occupied_columns = [any(mask[y][x] for y in range(height)) for x in range(width)]
    bounds: list[tuple[int, int, int, int]] = []
    column = 0
    while column < width:
        while column < width and not occupied_columns[column]:
            column += 1
        start = column
        while column < width and occupied_columns[column]:
            column += 1
        if start == column:
            continue
        end = column - 1
        rows = [y for y in range(height) for x in range(start, end + 1) if mask[y][x]]
        columns = [x for y in range(height) for x in range(start, end + 1) if mask[y][x]]
        bounds.append((min(columns), min(rows), max(columns) + 1, max(rows) + 1))
    return bounds


def _crop_mask(mask: list[list[bool]], bounds: tuple[int, int, int, int]) -> list[list[bool]]:
    left, top, right, bottom = bounds
    return [[mask[y][x] for x in range(left, right)] for y in range(top, bottom)]


def _features_for_digit(digit: list[list[bool]]) -> _DigitFeatures:
    height = len(digit)
    width = len(digit[0]) if height else 0
    if width == 0 or height == 0:
        raise ValueError("KuF occupancy image contained an empty digit segment.")

    def occupancy(x0: float, x1: float, y0: float, y1: float) -> float:
        xs = range(max(0, int(width * x0)), min(width, max(int(width * x1), int(width * x0) + 1)))
        ys = range(max(0, int(height * y0)), min(height, max(int(height * y1), int(height * y0) + 1)))
        return sum(digit[y][x] for y in ys for x in xs) / (len(xs) * len(ys))

    return _DigitFeatures(
        holes=_count_holes(digit),
        aspect=width / height,
        a=occupancy(0.2, 0.8, 0.0, 0.18),
        b=occupancy(0.6, 1.0, 0.14, 0.48),
        c=occupancy(0.6, 1.0, 0.52, 0.86),
        d=occupancy(0.2, 0.8, 0.82, 1.0),
        e=occupancy(0.0, 0.4, 0.52, 0.86),
        f=occupancy(0.0, 0.4, 0.14, 0.48),
        g=occupancy(0.18, 0.82, 0.42, 0.6),
        tr=occupancy(0.5, 1.0, 0.0, 0.5),
        bl=occupancy(0.0, 0.5, 0.5, 1.0),
    )


def _count_holes(digit: list[list[bool]]) -> int:
    height = len(digit)
    width = len(digit[0])
    seen = [[False for _ in range(width)] for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        for y in (0, height - 1):
            _enqueue_background(digit, seen, queue, x, y)
    for y in range(height):
        for x in (0, width - 1):
            _enqueue_background(digit, seen, queue, x, y)
    _flood_background(digit, seen, queue)

    holes = 0
    for y in range(height):
        for x in range(width):
            if digit[y][x] or seen[y][x]:
                continue
            holes += 1
            seen[y][x] = True
            queue.append((x, y))
            _flood_background(digit, seen, queue)
    return holes


def _enqueue_background(
    digit: list[list[bool]],
    seen: list[list[bool]],
    queue: deque[tuple[int, int]],
    x: int,
    y: int,
) -> None:
    if not digit[y][x] and not seen[y][x]:
        seen[y][x] = True
        queue.append((x, y))


def _flood_background(
    digit: list[list[bool]],
    seen: list[list[bool]],
    queue: deque[tuple[int, int]],
) -> None:
    height = len(digit)
    width = len(digit[0])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height and not digit[ny][nx] and not seen[ny][nx]:
                seen[ny][nx] = True
                queue.append((nx, ny))


def _classify_digit(features: _DigitFeatures) -> str:
    if features.holes >= 2:
        return "8"
    if features.holes == 1:
        if features.a < 0.5 and features.d < 0.45:
            return "4"
        if features.b < 0.45 and features.bl >= 0.4:
            return "6"
        if features.e < 0.46 and features.g > 0.4 and features.c > 0.5:
            return "9"
        return "0"
    if features.aspect < 0.42 or (features.aspect < 0.58 and features.b < 0.25 and features.c < 0.25):
        return "1"
    if features.a > 0.55 and features.d < 0.42 and features.f < 0.35 and features.e < 0.38:
        return "7"
    if features.f > max(features.b, features.e) and features.c > features.e + 0.15:
        return "5"
    if features.e > features.f and features.b > features.c * 0.75:
        return "2"
    return "3"
