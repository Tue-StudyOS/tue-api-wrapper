"""Review and explicitly perform Moodle quiz attempt actions."""
from __future__ import annotations

import argparse
import json
import sys

from .moodle_quiz_start import review_start, start_attempt
from .moodle_quiz_answer import review_answers, save_answers
from .moodle_quiz_finish import review_finish, finish_attempt
from .study_radar_runtime import make_client
from .ilias_quiz_start import review_ilias_start, start_ilias_attempt
from .ilias_quiz_attempt import fetch_question as ilias_question
from .ilias_quiz_answers import review_answers as ilias_review_answers, save_answers as ilias_save_answers
from .ilias_quiz_finish import review_finish as ilias_review_finish, finish_attempt as ilias_finish


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Review and perform Moodle quiz actions.')
    parser.add_argument('operation', choices=('read', 'review-start', 'start', 'review-answers', 'save-answers', 'review-finish', 'finish'))
    parser.add_argument('--service', choices=('moodle', 'ilias'), default='moodle')
    parser.add_argument('--target', required=True, type=int, help='Quiz ID for start; attempt ID for answers or finish.')
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('--answers-json', help='JSON mapping question field names to lists of values.')
    parser.add_argument('--review-sha256')
    parser.add_argument('--confirm', action='store_true')
    parser.add_argument('--env-file', default='.env')
    args = parser.parse_args(argv)
    if args.target < 1 or args.page < 0:
        parser.error('target must be positive and page nonnegative')
    if args.operation in {'start', 'save-answers', 'finish'} and (not args.confirm or not args.review_sha256):
        parser.error('write actions require --confirm and --review-sha256')
    if args.operation in {'review-answers', 'save-answers'} and not args.answers_json:
        parser.error('answer actions require --answers-json')
    if args.service == 'ilias' and args.page != 0:
        parser.error('ILIAS operates on the current question and does not support --page')
    try:
        answers = json.loads(args.answers_json) if args.answers_json else {}
        client, _ = make_client(args.env_file)
        try:
            if args.service == 'ilias':
                ilias = client.ilias.client
                if args.operation == 'read':
                    result = ilias_question(ilias, args.target)
                elif args.operation == 'review-start':
                    result = review_ilias_start(ilias, args.target)
                elif args.operation == 'start':
                    result = start_ilias_attempt(ilias, args.target, args.review_sha256, confirm=True)
                elif args.operation == 'review-answers':
                    result = ilias_review_answers(ilias, args.target, answers)
                elif args.operation == 'save-answers':
                    result = ilias_save_answers(ilias, args.target, answers, args.review_sha256, confirm=True)
                elif args.operation == 'review-finish':
                    result = ilias_review_finish(ilias, args.target)
                else:
                    result = ilias_finish(ilias, args.target, args.review_sha256, confirm=True)
            elif args.operation == 'read':
                result = client.moodle.quiz_attempt(args.target, page=args.page)
            elif args.operation == 'review-start':
                moodle = client.moodle.client
                result = review_start(moodle, args.target)
            elif args.operation == 'start':
                moodle = client.moodle.client
                result = start_attempt(moodle, args.target, args.review_sha256, confirm=True)
            elif args.operation == 'review-answers':
                moodle = client.moodle.client
                result = review_answers(moodle, args.target, args.page, answers)
            elif args.operation == 'save-answers':
                moodle = client.moodle.client
                result = save_answers(moodle, args.target, args.page, answers, args.review_sha256, confirm=True)
            elif args.operation == 'review-finish':
                moodle = client.moodle.client
                result = review_finish(moodle, args.target)
            else:
                moodle = client.moodle.client
                result = finish_attempt(moodle, args.target, args.review_sha256, confirm=True)
        finally:
            client.close()
        print(json.dumps(result, ensure_ascii=False))
        return int(result.get('outcome') in {'unknown', 'unverified'})
    except Exception as error:
        print(f'Moodle quiz error: {type(error).__name__}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
