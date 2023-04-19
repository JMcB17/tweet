"""Random thought saver"""

import platform
import re
import readline
import sqlite3
import sys
from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path

__version__ = '0.26.4'
NAME = 'jpytweet'
DB_SUFFIX = '.db'
CONFIG_DIR = Path('.config/').joinpath(NAME)
SHARE_DIR = Path('.local/share/').joinpath(NAME)
BASE_DIR = CONFIG_DIR
ARCHIVE_DIR = BASE_DIR.joinpath('archive/')
DB_DIR = BASE_DIR.joinpath('posts/')
ESCAPE_PATH_RE = re.compile(r'[^a-zA-Z0-9-]')
TIME_FORMAT = '%d/%m/%y %H:%M'


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('-V', '--version', action='version', version=__version__)
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


def escape_path(path: str) -> str:
    escaped = re.sub(ESCAPE_PATH_RE, '', path)
    return escaped


def get_home_dir() -> Path:
    if sys.gettrace is not None and sys.gettrace():
        # use local copy if debugging
        home_dir = Path.cwd().joinpath('instance')
        print(f'debug: {home_dir}', file=sys.stderr)
    else:
        home_dir = Path.home()
    return home_dir


def get_db_path() -> Path:
    hostname = platform.node()
    escaped = re.sub(r'[^a-zA-Z0-9-]', '', hostname)
    db_path = get_home_dir().joinpath(DB_DIR).joinpath(escaped).with_suffix(DB_SUFFIX)
    return db_path


def get_db() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tweets
            (timestamp DOUBLE NOT NULL PRIMARY KEY, content TEXT NOT NULL)
            """
        )

    return conn


def get_archive_db_path(archive_name: str) -> Path:
    archive_db_path = (
        get_home_dir()
        .joinpath(ARCHIVE_DIR)
        .joinpath(archive_name)
        .with_suffix(DB_SUFFIX)
    )
    return archive_db_path


def get_archive_db(archive_name: str) -> sqlite3.Connection:
    archive_path = get_archive_db_path(archive_name)

    if not archive_path.is_file():
        raise FileNotFoundError(f'No archive at {archive_path}')
    conn = sqlite3.connect(archive_path)
    return conn


def new_tweet(args: Namespace):
    content = args.tweet
    if content is None:
        content = input('New tweet:\n')
    elif isinstance(content, list):
        content = ' '.join(content)

    if not content:
        print('Tweet is empty')
        return
    # if len(content.encode('utf-8')) > TEXT_MAX_SIZE:
    #     print('Tweet is too long')
    #     return
    else:
        print(f'{len(content)} characters')

    conn = get_db()
    with conn:
        conn.execute(
            'INSERT INTO tweets (timestamp, content) VALUES (:timestamp, :content)',
            {'timestamp': datetime.now().timestamp(), 'content': content},
        )
    conn.close()
    print('Saved tweet')

    if args.pause:
        print('Press enter to exit')
        input()


def archive_db():
    db_path = get_db_path()
    if not db_path.is_file():
        print("Tweets file doesn't exist yet")
        return

    timestamp = datetime.now().isoformat()
    name = escape_path(timestamp)
    archive_db_path = get_archive_db_path(name)
    archive_db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.rename(archive_db_path)
    print('Archived old tweets file')

    get_db().close()
    print('Created new tweets file')


def list_tweets(args: Namespace):
    if args.archive:
        try:
            conn = get_archive_db(args.archive)
        except FileNotFoundError:
            print("That archive doesn't exist!")
            return
    else:
        conn = get_db()

    # -1 means no limit
    limit = args.n or -1
    cur = conn.execute('SELECT timestamp, content FROM tweets LIMIT :n', {'n': limit})
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
            timestamp = datetime.fromtimestamp(timestamp)
            timestamp = timestamp.strftime(TIME_FORMAT)
            tweet = list(tweet)
            tweet[0] = timestamp
            tweets[index] = tweet
    else:
        template = '{content}'

    output = [template.format(timestamp=t[0], content=t[1]) for t in tweets]
    print('\n'.join(output))


def list_archives():
    archive_dir = get_home_dir().joinpath(ARCHIVE_DIR)
    archives = archive_dir.iterdir()
    output = [a.stem for a in archives]
    print('\n'.join(output))


def run_from_args(args: Namespace):
    if args.subcommand is None:
        new_tweet(args)
    elif args.subcommand == 'list':
        list_tweets(args)
    elif args.subcommand == 'archive':
        archive_db()
    elif args.subcommand == 'list-archives':
        list_archives()


def main():
    parser = get_parser()
    args = parser.parse_args()
    try:
        readline.read_init_file()
    except FileNotFoundError:
        pass
    try:
        run_from_args(args)
    except KeyboardInterrupt:
        print('^C')
        sys.exit(1)


if __name__ == '__main__':
    main()
