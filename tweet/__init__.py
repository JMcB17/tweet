#!/usr/bin/env python

import time
import argparse
import sqlite3
from pathlib import Path


__version__ = '0.10.0'


CREATE_TABLE_SQL = """CREATE TABLE tweets
(timestamp DOUBLE(16, 6) PRIMARY KEY, content TEXT NOT NULL)"""
TEXT_MAX_SIZE = 65535
base_path = Path(__file__).parent
db_folder_path = base_path / 'tweets'
db_file_path = db_folder_path / 'tweets.db'
archive_folder_path = db_folder_path / 'archive'


parser = argparse.ArgumentParser(description='Random thought saver. Just run it, or use -h for more info.')
parser.add_argument('tweet', nargs='?', default=None,
                    help="'tweet' content. If you don't give it as an option, you'll be prompted to input it.")
parser.add_argument('--archive', action='store_true',
                    help='Archive the old tweets file and make a new one.')


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


def new_tweet(content):
    if content is None:
        content = input('New tweet:\n')

    timestamp = time.time()

    if not content:
        print('Tweet is empty')
        return
    if len(content.encode('utf-8')) > TEXT_MAX_SIZE:
        print('Tweet is too long')
        return

    conn, cur = get_db()
    cur.execute('INSERT INTO tweets VALUES (?,?)', (timestamp, content))
    conn.commit()
    conn.close()
    print('Saved tweet')


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


def main():
    args = parser.parse_args()
    if args.archive:
        archive()
    else:
        new_tweet(args.tweet)
    print('Press enter to exit')
    input()


if __name__ == '__main__':
    main()
