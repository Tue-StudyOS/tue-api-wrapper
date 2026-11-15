"""Compare successful observations without treating missing items as removals."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def compare_and_save(observation: dict[str, Any], path: Path) -> dict[str, Any]:
    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": 1, "sources": {}}
    if previous.get("version") != 1 or not isinstance(previous.get("sources"), dict):
        raise ValueError("Unsupported or invalid study radar snapshot")
    changes: dict[str, Any] = {}
    for name, source in observation["sources"].items():
        if source["status"] != "ok":
            changes[name] = {"status": "error", "error": source.get("error")}
            continue
        old = previous["sources"].get(name)
        current = {item["id"]: item for item in source["items"]}
        baseline = old is None
        old = old or {}
        changes[name] = {
            "status": "ok", "baseline": baseline,
            "added": [] if baseline else [item for key, item in current.items() if key not in old],
            "changed": [{"before": old[key], "after": item} for key, item in current.items() if key in old and old[key] != item],
            **{key: value for key, value in source.items() if key not in {"status", "items"}},
        }
        previous["sources"][name] = {**old, **current}
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".radar-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(previous, file, ensure_ascii=False)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return {"observed_at": observation.get("observed_at"), "scope": observation.get("scope"), "sources": changes,
            "note": "Missing items are not reported as removed; source coverage is bounded."}
