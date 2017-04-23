import json
import os
import shutil
import tempfile

from git import Repo

DIR = os.path.dirname(os.path.realpath(__file__))
SAMPLE_NB = os.path.join(DIR, 'sample_nb.ipynb')


class ProjectManager(object):
    """Class to create and destroy jupyter notebooks."""

    def __init__(self):
        self.file_count = 0
        self._repo = None
        self.test_directory = tempfile.mkdtemp()
        self.db_file = os.path.join(self.test_directory, 'carpo.db')

    def filename(self):
        """Generate unique file names for each new notebook"""
        self.file_count += 1
        return os.path.join(self.test_directory, 'sample_{}.ipynb'.format(self.file_count))

    def exists(self):
        """Check whether test directory exists"""
        return os.path.isdir(self.test_directory)

    def make_test_directory(self):
        if not self.exists():
            os.mkdir(self.test_directory)

    def delete_test_directory(self):
        if self.exists():
            shutil.rmtree(self.test_directory)

    @property
    def repo(self):
        if self._repo is None:
            self._repo = Repo.init(self.test_directory)
        return self._repo

    def commit(self, *files):
        """Commit all files in the repo"""
        to_add = self.repo.untracked_files[:]
        to_add.extend(files)

        if to_add:
            self.repo.index.add(to_add)
            return self.repo.index.commit('WIP').hexsha

    def add_nb_with_input(self, nb_input):
        """Add a notebook to the directory with the given input string."""
        new_filename = self.filename()
        shutil.copyfile(SAMPLE_NB, new_filename)
        self.set_nb_input(new_filename, nb_input)

        # Make sure default output stays the same
        assert self.get_output(new_filename) == '0'
        return new_filename

    def set_nb_input(self, nb_name, nb_input):
        """Set value of the first cell"""
        with open(nb_name, 'r') as buff:
            nb = json.load(buff)
        nb['cells'][0]['source'][0] = nb_input
        with open(nb_name, 'w') as buff:
            json.dump(nb, buff)

    def get_output(self, nb_name):
        """Read output from the first cell of the given notebook."""
        with open(nb_name, 'r') as buff:
            nb = json.load(buff)
        return nb['cells'][0]['outputs'][0]['data']['text/plain'][0]
