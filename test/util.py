import json
import os
import shutil
import tempfile

from git import Repo
from jupyter_client.kernelspec import find_kernel_specs

DIR = os.path.dirname(os.path.realpath(__file__))
SAMPLE_NB = os.path.join(DIR, 'sample_nb.ipynb')


class ProjectManager(object):
    """Class to create and destroy jupyter notebooks."""

    def __init__(self):
        self.file_count = 0
        self._repo = None
        self.test_directory = tempfile.mkdtemp()
        self.db_file = os.path.join(self.test_directory, 'carpo.db')
        self.kernelspec = self.get_kernelspec()

    def filename(self):
        """Generate unique file names for each new notebook"""
        self.file_count += 1
        return os.path.join(self.test_directory, 'sample_{}.ipynb'.format(self.file_count))

    def get_kernelspec(self):
        """Use an available kernelspec for test notebook"""
        for name in find_kernel_specs():
            if name.startswith('python'):
                return name
        raise RuntimeError('No python kernel found to run notebooks!')

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
        self.set_nb_kernel(new_filename)
        self.set_nb_input(new_filename, nb_input)

        # Make sure default output stays the same
        assert self.get_output(new_filename) == '0'
        return new_filename

    def _load_nb(self, nb_name):
        """Helper to load notebook as json"""
        with open(nb_name, 'r') as buff:
            return json.load(buff)

    def _dump_nb(self, nb, nb_name):
        """Helper to save notebook"""
        with open(nb_name, 'w') as buff:
            return json.dump(nb, buff)

    def set_nb_kernel(self, nb_name):
        """Set the kernel for the notebook."""
        nb = self._load_nb(nb_name)
        nb['metadata']['kernelspec']['name'] = self.kernelspec
        self._dump_nb(nb, nb_name)

    def set_nb_input(self, nb_name, nb_input):
        """Set value of the first cell"""
        nb = self._load_nb(nb_name)
        nb['cells'][0]['source'][0] = nb_input
        self._dump_nb(nb, nb_name)

    def get_output(self, nb_name):
        """Read output from the first cell of the given notebook."""
        with open(nb_name, 'r') as buff:
            nb = json.load(buff)
        return nb['cells'][0]['outputs'][0]['data']['text/plain'][0]
