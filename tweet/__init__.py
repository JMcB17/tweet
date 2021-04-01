#!/usr/bin/env python

import time
import argparse
import sqlite3
from pathlib import Path


__version__ = '0.24.0'


CREATE_TABLE_SQL = """CREATE TABLE tweets
(timestamp DOUBLE(16, 6) PRIMARY KEY, content TEXT NOT NULL);
CREATE TABLE keyhole
(plaintext TEXT NOT NULL, ciphertext BLOB NOT NULL);
INSERT INTO keyhole VALUES ('lorem ipsum dolor sit amet', 'lorem ipsum dolor sit amet');"""
TEXT_MAX_SIZE = 65535
base_path = Path.home()
db_folder_path = base_path / 'tweets'
db_file_path = db_folder_path / 'tweets.db'
archive_folder_path = db_folder_path / 'archive'


parser = argparse.ArgumentParser(description='Random thought saver. Just run it, or use -h for more info.')
parser.add_argument('--version', action='version', version=__version__)
parser.add_argument('-t', '--tweet',
                    help="'tweet' content. If you don't give it as an option, you'll be prompted to input it")
subparsers = parser.add_subparsers(help='subcommands', dest='subcommand')

archive_parser = subparsers.add_parser(name='archive',
                                       help='archive the old tweets file and make a new one')

list_parser = subparsers.add_parser(name='list',
                                    help='list tweets')
list_parser.add_argument('-a', '--archive',
                         help='use this archive file instead of the current file')
list_parser.add_argument('-l', action='store_true',
                         help='show ids as well')
list_parser.add_argument('-i', '--id-only', action='store_true', dest='i',
                         help='show only ids')
list_parser.add_argument('-t', '--timestamp', action='store_true', dest='t',
                         help='show human readable timestamps as well')
list_parser.add_argument('-n', '--max-count', type=int, dest='n',
                         help='limit the number of tweets to output')

list_archives_parser = subparsers.add_parser(name='list-archives',
                                             help='list archives')


def get_db():
    if not db_folder_path.is_dir():
        db_folder_path.mkdir()
    create_table = not db_file_path.is_file()

    conn = sqlite3.connect(db_file_path)
    cur = conn.cursor()

    if create_table:
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()

    return conn, cur


def new_tweet(args):
    content = args.tweet
    pause = content is None
    if content is None:
        content = input('New tweet:\n')
    elif isinstance(content, list):
        content = ' '.join(content)

    timestamp = time.time()

    if not content:
        print('Tweet is empty')
        return
    if len(content.encode('utf-8')) > TEXT_MAX_SIZE:
        print('Tweet is too long')
        return
    else:
        print(f'{len(content)} characters')

    conn, cur = get_db()
    cur.execute('INSERT INTO tweets VALUES (?,?)', (timestamp, content))
    conn.commit()
    conn.close()
    print('Saved tweet')

    if pause:
        print('Press enter to exit')
        input()


def archive():
    timestamp = time.time()

    if not db_file_path.is_file():
        print("Tweets file doesn't exist yet")
        return

    new_db_file_path = archive_folder_path.joinpath(str(int(timestamp))).with_suffix(db_file_path.suffix)
    if not archive_folder_path.is_dir():
        archive_folder_path.mkdir()
    db_file_path.rename(new_db_file_path)
    print('Archived old tweets file')

    conn, cur = get_db()
    conn.close()
    print('Created new tweets file')


def get_archive_db(archive_name):
    archive_file_path = archive_folder_path.joinpath(archive_name).with_suffix('.db')

    if not archive_file_path.is_file():
        raise FileNotFoundError
    else:
        conn = sqlite3.connect(archive_file_path)
        cur = conn.cursor()
        return conn, cur


def list_tweets(args):
    if args.archive:
        try:
            conn, cur = get_archive_db(args.archive)
        except FileNotFoundError:
            print("That archive doesn't exist!")
            return
    else:
        conn, cur = get_db()

    if args.n is not None:
        cur.execute('SELECT * FROM tweets LIMIT ?', (args.n,))
    else:
        cur.execute('SELECT * FROM tweets')
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
    archives = archive_folder_path.iterdir()
    output = [a.stem for a in archives]
    print('\n'.join(output))


def main():
    args = parser.parse_args()
    if args.subcommand is None:
        new_tweet(args)
    elif args.subcommand == 'archive':
        archive()
    elif args.subcommand == 'list':
        list_tweets(args)
    elif args.subcommand == 'list-archives':
        list_archives()


if __name__ == '__main__':
    main()
