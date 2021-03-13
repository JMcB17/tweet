#!/usr/bin/env python

import time
import argparse
import sqlite3
from pathlib import Path


__version__ = '0.9.0'


CREATE_TABLE_SQL = """CREATE TABLE tweets
(timestamp DOUBLE(16, 6) PRIMARY KEY, content TEXT NOT NULL)"""
TEXT_MAX_SIZE = 65535
base_path = Path(__file__).parent
db_folder_path = base_path / 'tweets'


parser = argparse.ArgumentParser(description='Random thought saver. Just run it, or use -h for more info.')
parser.add_argument('tweet', nargs='?', default=None,
                    help="'tweet' content. If you don't give it as an option, you'll be prompted to input it.")
args = parser.parse_args()


def get_db():
    if not db_folder_path.is_dir():
        db_folder_path.mkdir()
    db_file_path = db_folder_path / 'tweets.db'
    create_table = not db_file_path.is_file()

    conn = sqlite3.connect(db_file_path)
    cur = conn.cursor()

    if create_table:
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()

    return conn, cur


def new_tweet(content=args.tweet):
    if content is None:
        content = input('New tweet:\n')

    if not content:
        print('Tweet is empty')
        return
    if len(content.encode('utf-8')) > TEXT_MAX_SIZE:
        print('Tweet is too long')
        return

    timestamp = time.time()

    conn, cur = get_db()
    cur.execute('INSERT INTO tweets VALUES (?,?)', (timestamp, content))
    conn.commit()
    conn.close()
    print('Saved tweet')
    print('Press enter to exit')
    input()


def main():
    new_tweet()


if __name__ == '__main__':
    main()
