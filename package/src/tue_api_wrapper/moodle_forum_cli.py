"""Review and explicitly post Moodle forum messages."""
from __future__ import annotations

import argparse
import json
import sys

from .moodle_forum_write import publish_post, review_post
from .ilias_forum_write import publish_ilias_post, review_ilias_post
from .study_radar_runtime import make_client


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Review and post a Moodle or ILIAS forum discussion or reply.')
    parser.add_argument('operation', choices=('review', 'publish'))
    parser.add_argument('--mode', choices=('new', 'reply'), required=True)
    parser.add_argument('--service', choices=('moodle', 'ilias'), default='moodle')
    parser.add_argument('--target', required=True, help='Moodle forum/post ID or ILIAS forum/thread target.')
    parser.add_argument('--parent-id', help='Parent ILIAS post ID for a reply.')
    parser.add_argument('--subject', required=True)
    parser.add_argument('--message', required=True)
    parser.add_argument('--review-sha256')
    parser.add_argument('--confirm', action='store_true')
    parser.add_argument('--env-file', default='.env')
    args = parser.parse_args(argv)
    if args.operation == 'publish' and (not args.confirm or not args.review_sha256):
        parser.error('publish requires --confirm and --review-sha256')
    if args.service == 'moodle' and (not args.target.isascii() or not args.target.isdigit() or int(args.target) < 1):
        parser.error('Moodle target must be a positive numeric ID')
    try:
        client, _ = make_client(args.env_file)
        try:
            if args.service == 'ilias' and args.operation == 'review':
                result = review_ilias_post(client.ilias.client, args.mode, args.target, args.subject, args.message, args.parent_id)
            elif args.service == 'ilias':
                result = publish_ilias_post(client.ilias.client, args.mode, args.target, args.subject, args.message,
                                            args.review_sha256, confirm=True, parent_id=args.parent_id)
            elif args.operation == 'review':
                result = review_post(client.moodle.client, args.mode, int(args.target), args.subject, args.message)
            else:
                result = publish_post(client.moodle.client, args.mode, int(args.target), args.subject, args.message,
                                      args.review_sha256, confirm=True)
        finally:
            client.close()
        print(json.dumps(result, ensure_ascii=False))
        return int(args.operation == 'publish' and result['outcome'] != 'confirmed')
    except Exception as error:
        print(f'Forum error: {type(error).__name__}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
