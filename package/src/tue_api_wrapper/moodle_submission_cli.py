"""Review, save, finalize, or verify one Moodle file submission."""
from __future__ import annotations

import argparse
import json
import sys

from .moodle_submission_final import review_final, submit_final
from .moodle_submission_write import file_details, review_file, save_file, verify_file_receipt
from .study_radar_runtime import make_client


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Review and explicitly submit a Moodle assignment file.')
    parser.add_argument('operation', choices=('review', 'save', 'review-final', 'submit', 'verify'))
    parser.add_argument('--assignment-id', type=int, required=True)
    parser.add_argument('--file', required=True, help='Local file whose contents are reviewed and verified.')
    parser.add_argument('--sha256', help='File SHA-256 from the review.')
    parser.add_argument('--review-sha256', help='Assignment review hash from review.')
    parser.add_argument('--confirmation-sha256', help='Moodle confirmation text hash from review-final.')
    parser.add_argument('--confirm', action='store_true', help='Explicitly authorize this write.')
    parser.add_argument('--accept-statement', action='store_true', help='Accept the reviewed Moodle statement.')
    parser.add_argument('--env-file', default='.env')
    args = parser.parse_args(argv)
    if args.assignment_id < 1:
        parser.error('--assignment-id must be positive')
    if args.operation in {'save', 'submit'} and (not args.confirm or not args.sha256):
        parser.error('save and submit require --confirm and the reviewed --sha256')
    if args.operation == 'submit' and not args.confirmation_sha256:
        parser.error('submit requires --confirmation-sha256 from review-final')
    if args.operation == 'save' and not args.review_sha256:
        parser.error('save requires --review-sha256 from review')
    try:
        client, _ = make_client(args.env_file)
        try:
            moodle = client.moodle.client
            if args.operation == 'review':
                result = review_file(moodle, args.assignment_id, args.file)
            elif args.operation == 'save':
                result = save_file(moodle, args.assignment_id, args.file, args.sha256, args.review_sha256, confirm=True)
            elif args.operation == 'review-final':
                result = review_final(moodle, args.assignment_id, args.file)
            elif args.operation == 'submit':
                result = submit_final(moodle, args.assignment_id, args.file, args.sha256,
                                      args.confirmation_sha256, confirm=True, accept_statement=args.accept_statement)
            else:
                result = verify_file_receipt(moodle, args.assignment_id, file_details(args.file))
        finally:
            client.close()
        print(json.dumps(result, ensure_ascii=False))
        if args.operation == 'submit':
            return int(result['outcome'] != 'submitted')
        return int(args.operation in {'save', 'verify'} and result['outcome'] == 'unknown')
    except Exception as error:
        print(f'Moodle submission error: {type(error).__name__}: {error}', file=sys.stderr)
        if args.operation in {'save', 'submit'}:
            print('If a request was sent, the outcome may be unknown. Inspect Moodle before retrying.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
