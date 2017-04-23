"""Wrapper for database operations."""
from collections import namedtuple
from datetime import datetime
import os
import sqlite3
import time

import click
from git import Repo, InvalidGitRepositoryError
from terminaltables import SingleTable


Row = namedtuple('Row', ['name', 'type', 'formatter'])

FIELDS = (
    Row('notebook_path', 'TEXT', str),
    Row('git_sha', 'TEXT', str),
    Row('git_root', 'TEXT', str),
    Row('success', 'INTEGER', lambda j: str(bool(j))),
    Row('time', 'NUMERIC', '{:.2f}s'.format),
    Row('run_date', 'INTEGER', lambda j: datetime.fromtimestamp(j).strftime('%H:%M:%S on %B %d, %Y')),
)
FORMATTERS = {field.name: field.formatter for field in FIELDS}
TABLE_KEYS = ('time', 'run_date', 'git_sha')

CREATE_SCHEMA = "CREATE TABLE notebooks ({})".format(',\n'.join(['{0.name} {0.type}'.format(row) for row in FIELDS]))
INSERT_SCHEMA = "INSERT INTO notebooks VALUES (?, ?, ?, ?, ?, ?)"


def dict_factory(cursor, row):
    """Factory to return query results as dictionaries."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def format_result(result):
    """Consistent formatting of results"""
    formatted = {}
    if result.get('success', True):
        color = 'green'
    else:
        color = 'red'
    for key, value in result.items():
        if key in TABLE_KEYS:
            formatted[key] = click.style(FORMATTERS.get(key, str)(value), fg=color)
    return formatted


def results_to_table(list_of_results, title):
    """Format query results as a table."""
    rows = [TABLE_KEYS]
    for result in list_of_results:
        formatted = format_result(result)
        rows.append([formatted[key] for key in rows[0]])
    return SingleTable(rows, title=title).table


def get_git_repo(notebook_path):
    """If the notebook is checked into git, fetch the repository"""
    try:
        return Repo(notebook_path, search_parent_directories=True)
    except InvalidGitRepositoryError:
        return None


def get_git_info(notebook_path):
    """Fetch sha and root directory name for notebook, if it is checked into git."""
    repo = get_git_repo(notebook_path)
    if repo is None:
        return '', ''
    return os.path.basename(repo.working_dir), repo.commit().hexsha


def sort_git_shas(notebook_path, records, default_branch='master'):
    """Sort a list of shas on a given branch."""
    repo = get_git_repo(notebook_path)
    if repo is None:
        return records
    commits = [c.hexsha for c in repo.iter_commits(default_branch)]
    ordered, not_ordered = [], []
    for record in records:
        if record['git_sha'] in commits:
            ordered.append(record)
        else:
            not_ordered.append(record)

    return sorted(ordered, key=lambda record: commits.index(record['git_sha'])) + not_ordered


def get_default_home():
    """Use user's home directory as a default"""
    return os.path.join(os.path.expanduser('~'), '.carpo.db')


class DB(object):
    """Wrapper for sqlite.  Provides context manager and dictionary iterator."""

    def __init__(self, path):
        """Initialize with path to database file"""
        self.path = path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Start context manager with dictionary row factory"""
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = dict_factory
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        """Commit and close connection on exit."""
        self.conn.commit()
        self.conn.close()


class Records(object):
    """Interact with the database"""

    def __init__(self, path):
        """Initialize with path to the database."""
        self.path = path
        self._db = DB(self.path)
        self._create_table()

    def _create_table(self):
        if not os.path.exists(self.path):
            with self._db as cur:
                cur.execute(CREATE_SCHEMA)

    def record_outcome(self, outcome):
        """Insert a named tuple into the database"""
        git_root, git_sha = get_git_info(outcome.path)
        run_date = int(time.time())
        result = (outcome.path, git_sha, git_root, int(outcome.success), outcome.run_time, run_date)
        with self._db as cur:
            cur.execute(INSERT_SCHEMA, result)

    def already_run(self, notebook_path):
        """Check if a notebook has already run under the given git sha"""
        _, git_sha = get_git_info(notebook_path)
        if not git_sha:
            return False
        with self._db as cur:
            cur.execute("""SELECT * FROM notebooks
                        WHERE success=1 AND notebook_path=? AND git_sha=? LIMIT 1""",
                        (notebook_path, git_sha))
            return bool(cur.fetchall())

    def status(self, notebook_path, branch='master'):
        """Get a list of times the notebook has run successfully sorted by git sha, then date"""
        with self._db as cur:
            cur.execute("""SELECT * FROM notebooks WHERE notebook_path=?
                        ORDER BY run_date DESC""", (notebook_path,))
            results = cur.fetchall()
        return results_to_table(sort_git_shas(notebook_path, results, default_branch=branch),
                                title=notebook_path)
