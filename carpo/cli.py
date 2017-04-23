"""Main command line interface."""
from collections import namedtuple
import os
import time

import click
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

from .record import Records, get_default_home


NotebookRun = namedtuple('NotebookRun', ['path', 'success', 'run_time', 'message'])


@click.group()
def cli():
    """Base for cli commands."""
    pass


def execute_notebook(notebook_path):
    """Run and overwrite a notebook file."""
    executor = ExecutePreprocessor(timeout=-1)
    with open(notebook_path, 'r') as buff:
        notebook = nbformat.read(buff, as_version=nbformat.NO_CONVERT)
    try:
        start_time = time.time()
        executor.preprocess(notebook, {'metadata': {'path': os.path.dirname(notebook_path)}})
        run_time = time.time() - start_time

    except KeyboardInterrupt:
        raise

    except BaseException as exc:
        run_time = time.time() - start_time
        success = False
        msg = str(exc)
    else:
        with open(notebook_path, 'w') as buff:
            nbformat.write(notebook, buff)
        success = True
        msg = ''
    return success, run_time, msg


def log_outcome(outcome):
    """Log a notebook outcome with click.secho"""
    if outcome.success:
        color = 'green'
        verb = 'succeeded'
    else:
        color = 'red'
        verb = 'failed'

    message = '{} {} in {:.1f}s'.format(os.path.basename(outcome.path), verb, outcome.run_time)
    click.secho(message, fg=color)
    if outcome.message:
        click.secho(outcome.message, fg=color)


@cli.command()
@click.argument('notebooks', type=click.Path(), nargs=-1)
@click.option('--db-file', default=get_default_home(),
              help='Location to store results', show_default=True)
@click.option('--force', is_flag=True, help='Run notebooks even if they have been run at this sha')
def run(notebooks, db_file, force):
    """Try to re-run all notebooks.  Print failures at end."""
    records = Records(db_file)
    if not force:
        notebooks = [nb_path for nb_path in notebooks if not records.already_run(nb_path)]
    for notebook_path in sorted(notebooks):
        click.secho('Executing {}'.format(os.path.basename(notebook_path)))
        success, run_time, msg = execute_notebook(notebook_path)
        outcome = NotebookRun(notebook_path, success, run_time, msg)
        records.record_outcome(outcome)
        log_outcome(outcome)


@cli.command()
@click.argument('notebooks', type=click.Path(), nargs=-1)
@click.option('--db-file', default=get_default_home(),
              help='Location to store results', show_default=True)
def list(notebooks, db_file):
    records = Records(db_file)
    results = []
    for filename in notebooks:
        results.extend(records.list(filename))
    click.secho(str(results, header='keys'))
