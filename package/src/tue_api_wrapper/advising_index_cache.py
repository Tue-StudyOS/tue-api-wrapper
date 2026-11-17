from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile

from .advising_discovery_models import AdvisingDiscoveryError, AdvisingDiscoveryPage, AdvisingIndex, AdvisingPassage
from .advising_models import AdvisingLink
from .config import AlmaParseError


class AdvisingIndexCache:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / '.tue-api-wrapper' / 'advising-discovery.json'

    def load(self) -> AdvisingIndex | None:
        try:
            raw = self.path.read_text(encoding='utf-8')
        except FileNotFoundError:
            return None
        try:
            payload = json.loads(raw)
            if payload['version'] != 1:
                raise ValueError('unsupported index version')
            index = payload['index']
            pages = tuple(AdvisingDiscoveryPage(**page) for page in index['pages'])
            passages = tuple(AdvisingPassage(**{**item, 'links': tuple(AdvisingLink(**link) for link in item['links'])})
                             for item in index['passages'])
            errors = tuple(AdvisingDiscoveryError(**error) for error in index['errors'])
            return AdvisingIndex(**{**index, 'pages': pages, 'passages': passages, 'errors': errors})
        except (ValueError, TypeError, KeyError) as error:
            raise AlmaParseError(f'The advising index at {self.path} is invalid: {error}') from error

    def save(self, index: AdvisingIndex) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=self.path.parent, delete=False) as file:
                temporary = Path(file.name)
                json.dump({'version': 1, 'index': asdict(index)}, file, ensure_ascii=False)
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
