"""Review and explicitly confirm a Moodle final-submission form."""
from __future__ import annotations

import hashlib
import json

from .config import AlmaParseError
from .moodle_submission_forms import get_form, parse_form
from .moodle_submission_write import file_details, verify_file_receipt


def _confirmation_hash(text: str, receipt: dict) -> str:
    stable = [row for row in receipt['submission']
              if row['label'].strip().casefold() not in {'verbleibende zeit', 'time remaining'}]
    content = {'text': text, 'assignment_id': receipt['assignment_id'], 'file': receipt['file'], 'submission': stable}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def review_final(client, assignment_id: int, path: str) -> dict:
    file = file_details(path)
    receipt = verify_file_receipt(client, assignment_id, file)
    if receipt['outcome'] != 'draft':
        raise AlmaParseError('A matching saved draft could not be verified; inspect Moodle before submitting')
    html, url = get_form(client, assignment_id, 'submit')
    _, form, _ = parse_form(html, url, assignment_id, 'confirmsubmit')
    boxes = form.select('input[type="checkbox"]')
    if any(b.get('name') != 'submissionstatement' for b in boxes) or len(boxes) > 1:
        raise AlmaParseError('Moodle requires an unsupported acknowledgement')
    # Include the full visible text so the reviewer sees group and declaration notices.
    text = form.get_text(' ', strip=True)
    digest = _confirmation_hash(text, receipt)
    return {'assignment_id': assignment_id, 'file': file, 'receipt': receipt,
            'confirmation_text': text, 'confirmation_sha256': digest,
            'requires_statement': bool(boxes)}


def submit_final(client, assignment_id: int, path: str, expected_sha256: str,
                 confirmation_sha256: str, *, confirm: bool, accept_statement: bool = False) -> dict:
    if not confirm:
        raise ValueError('Explicit confirmation is required')
    reviewed = review_final(client, assignment_id, path)
    if reviewed['file']['sha256'] != expected_sha256 or reviewed['confirmation_sha256'] != confirmation_sha256:
        raise ValueError('File or Moodle confirmation text changed since review')
    if reviewed['requires_statement'] and not accept_statement:
        raise ValueError('The Moodle submission statement must be explicitly accepted')
    html, url = get_form(client, assignment_id, 'submit')
    _, form, fields = parse_form(html, url, assignment_id, 'confirmsubmit')
    if _confirmation_hash(form.get_text(' ', strip=True), reviewed['receipt']) != confirmation_sha256:
        raise ValueError('Moodle confirmation text changed since review')
    boxes = form.select('input[type="checkbox"]')
    if any(b.get('name') != 'submissionstatement' for b in boxes) or len(boxes) > 1:
        raise AlmaParseError('Moodle requires an unsupported acknowledgement')
    if boxes:
        if not accept_statement:
            raise ValueError('The Moodle submission statement must be explicitly accepted')
        fields['submissionstatement'] = boxes[0].get('value', '1')
    try:
        response = client.session.post(f'{client.base_url}/mod/assign/view.php', data=fields,
                                       timeout=client.timeout_seconds, allow_redirects=False)
        response.raise_for_status()
        if response.status_code not in {200, 302, 303}:
            raise AlmaParseError('Final submission response was not recognized')
        return verify_file_receipt(client, assignment_id, reviewed['file'])
    except Exception:
        raise AlmaParseError('Final submission outcome is unknown; inspect Moodle before retrying') from None
