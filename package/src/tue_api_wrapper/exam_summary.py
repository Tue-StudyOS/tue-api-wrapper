from __future__ import annotations

import math
from collections.abc import Sequence

from .models import AlmaExamNode


def summarize_exam_records(exams: Sequence[AlmaExamNode]) -> tuple[int, float]:
    """Summarize leaf records so parent totals are not counted twice."""
    passed = 0
    credits = 0.0
    for index, exam in enumerate(exams):
        if index + 1 < len(exams) and exams[index + 1].level > exam.level:
            continue
        status = (exam.status or "").strip().upper()
        grade = _number(exam.grade)
        if status in {"BE", "PASSED", "BESTANDEN"} or (
            not status and grade is not None and 1 <= grade <= 4
        ):
            passed += 1
        cp = _number(exam.cp)
        if cp is not None and cp >= 0:
            credits += cp
    return passed, round(credits, 1)


def _number(value: str | None) -> float | None:
    try:
        result = float((value or "").strip().replace(",", "."))
    except ValueError:
        return None
    return result if math.isfinite(result) else None
