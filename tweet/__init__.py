#!/usr/bin/env python

import sqlite3
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path
from sys import gettrace

__version__ = '0.24.0'

if gettrace is not None and gettrace():
    HOME_DIR = Path.cwd().joinpath('instance')
    print(HOME_DIR)
else:
    HOME_DIR = Path.home()

NAME = 'jpytweet'
DB_SUFFIX = '.db'
CONFIG_DIR = HOME_DIR.joinpath('.config/').joinpath(NAME)
SHARE_DIR = HOME_DIR.joinpath('.local/share/').joinpath(NAME)
ARCHIVE_DIR = SHARE_DIR.joinpath('archive')
DB_PATH = SHARE_DIR.joinpath(f'posts').with_suffix(DB_SUFFIX)


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description='Random thought saver. Just run it, or use -h for more info.'
    )
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument(
        '-t',
        '--tweet',
        help="'tweet' content. If you don't give it as an option, you'll be prompted to input it",
    )
    parser.add_argument('-p', '--pause', help='wait for enter after typing')

    # subcommands
    subparsers = parser.add_subparsers(help='subcommands', dest='subcommand')

    list_parser = subparsers.add_parser(name='list', help='list tweets')
    list_parser.add_argument(
        '-a', '--archive', help='use this archive file instead of the current file'
    )
    list_parser.add_argument('-l', action='store_true', help='show ids as well')
    list_parser.add_argument(
        '-i', '--id-only', action='store_true', dest='i', help='show only ids'
    )
    list_parser.add_argument(
        '-t',
        '--timestamp',
        action='store_true',
        dest='t',
        help='show human readable timestamps as well',
    )
    list_parser.add_argument(
        '-n',
        '--max-count',
        type=int,
        dest='n',
        help='limit the number of tweets to output',
    )

    subparsers.add_parser(
        name='archive', help='archive the old tweets file and make a new one'
    )
    subparsers.add_parser(name='list-archives', help='list archives')

    return parser


def get_db() -> sqlite3.Connection:
    SHARE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tweets
        (timestamp DOUBLE NOT NULL PRIMARY KEY, content TEXT NOT NULL)
        """
    )
    conn.commit()

    return conn


def new_tweet(args: Namespace):
    content = args.tweet
    if content is None:
        content = input('New tweet:\n')
    elif isinstance(content, list):
        content = ' '.join(content)

    timestamp = time.time()

    if not content:
        print('Tweet is empty')
        return
    # if len(content.encode('utf-8')) > TEXT_MAX_SIZE:
    #     print('Tweet is too long')
    #     return
    else:
        print(f'{len(content)} characters')

    conn = get_db()
    conn.execute('INSERT INTO tweets VALUES (?,?)', (timestamp, content))
    conn.commit()
    conn.close()
    print('Saved tweet')

    if args.pause:
        print('Press enter to exit')
        input()


def archive():
    if not DB_PATH.is_file():
        print("Tweets file doesn't exist yet")
        return

    timestamp = str(int(time.time()))
    new_db_file_path = ARCHIVE_DIR.joinpath(timestamp).with_suffix(DB_SUFFIX)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.rename(new_db_file_path)
    print('Archived old tweets file')

    conn = get_db()
    conn.close()
    print('Created new tweets file')


def get_archive_db(archive_name: str):
    archive_file_path = ARCHIVE_DIR.joinpath(archive_name).with_suffix('.db')

    if not archive_file_path.is_file():
        raise FileNotFoundError
    else:
        conn = sqlite3.connect(archive_file_path)
        return conn


def list_tweets(args: Namespace):
    if args.archive:
        try:
            conn = get_archive_db(args.archive)
        except FileNotFoundError:
            print("That archive doesn't exist!")
            return
    else:
        conn = get_db()

    if args.n is not None:
        cur = conn.execute('SELECT * FROM tweets LIMIT ?', (args.n,))
    else:
        cur = conn.execute('SELECT * FROM tweets')
    tweets = cur.fetchall()
    conn.close()

    if args.l:
        template = '{timestamp} {content}'
    elif args.i:
        template = '{timestamp}'
    elif args.t:
        template = '{timestamp} {content}'
        for index, tweet in enumerate(tweets):
            timestamp = tweet[0]
            timestamp = time.localtime(timestamp)
            timestamp = time.strftime('%d/%m/%y %H:%M', timestamp)
            tweet = list(tweet)
            tweet[0] = timestamp
            tweets[index] = tweet
    else:
        template = '{content}'

    output = [template.format(timestamp=t[0], content=t[1]) for t in tweets]
    print('\n'.join(output))


def list_archives():
    archives = ARCHIVE_DIR.iterdir()
    output = [a.stem for a in archives]
    print('\n'.join(output))


def main():
    parser = get_parser()
    args = parser.parse_args()
    if args.subcommand is None:
        new_tweet(args)
    elif args.subcommand == 'list':
        list_tweets(args)
    elif args.subcommand == 'archive':
        archive()
    elif args.subcommand == 'list-archives':
        list_archives()


if __name__ == '__main__':
    main()
