"""Wrapper for database operations."""
from collections import namedtuple
import os
import sqlite3
import time

from git import Repo, InvalidGitRepositoryError


CREATE_SCHEMA = """
    CREATE TABLE notebooks (
        notebook_path TEXT,
        git_sha TEXT,
        git_root TEXT,
        success INTEGER,
        time NUMERIC,
        run_date INTEGER)
"""

INSERT_SCHEMA = "INSERT INTO notebooks VALUES (?, ?, ?, ?, ?, ?)"


def namedtuple_factory(cursor, row):
    """Return database results as namedtuples

    Usage:
    con.row_factory = namedtuple_factory
    """
    fields = [col[0] for col in cursor.description]
    Row = namedtuple("Row", fields)
    return Row(*row)


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
    basename = os.path.basename(repo.working_dir)
    sha = repo.commit().hexsha
    return basename, sha


def sort_git_shas(notebook_path, records, default_branch='master'):
    """Sort a list of shas on a given branch."""
    repo = get_git_repo(notebook_path)
    if repo is None:
        return records
    commits = [c.hexsha for c in repo.iter_commits(default_branch)]
    ordered, not_ordered = [], []
    for record in records:
        if record.git_sha in commits:
            ordered.append(record)
        else:
            not_ordered.append(record)

    return sorted(ordered, key=lambda record: commits.index(record.sha)) + not_ordered


def get_default_home():
    """Use user's home directory as a default"""
    return os.path.join(os.path.expanduser('~'), '.carpo.db')


class DB(object):
    """Wrapper for sqlite.  Provides context manager and namedtuple iterator."""

    def __init__(self, path):
        """Initialize with path to database file"""
        self.path = path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Start context manager with namedtuple row factory"""
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = namedtuple_factory
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
            cur.execute("""SELECT 1 FROM notebooks
                        WHERE success=1 AND notebook_path=? AND git_sha=? LIMIT 1""",
                        (notebook_path, git_sha))
            result = cur.fetchall()
            print(bool(result))
        return bool(result)

    def list(self, notebook_path, branch='master'):
        """Get a list of times the notebook has run successfully sorted by git sha, then date"""
        with self._db as cur:
            cur.execute("""SELECT * FROM notebooks WHERE success=1 AND notebook_path=?
                        ORDER BY run_date DESC""", (notebook_path,))
            results = cur.fetchall()
        return sort_git_shas(notebook_path, results, default_branch=branch)
