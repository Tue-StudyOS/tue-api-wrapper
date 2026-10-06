from datetime import date

import pytest

from tue_api_wrapper.portal_common import current_dashboard_term


@pytest.mark.parametrize("day,expected", [
    (date(2026, 3, 31), "Winter 2025/26"),
    (date(2026, 4, 1), "Sommer 2026"),
    (date(2026, 9, 30), "Sommer 2026"),
    (date(2026, 10, 1), "Winter 2026/27"),
    (date(2027, 1, 1), "Winter 2026/27"),
])
def test_current_semester_boundaries(day: date, expected: str) -> None:
    assert current_dashboard_term(day) == expected
