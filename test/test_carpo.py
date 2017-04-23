from click.testing import CliRunner

from carpo.cli import run
from util import ProjectManager


class TestCarpo(object):
    @classmethod
    def setup_class(cls):
        cls.pm = ProjectManager()
        cls.pm.make_test_directory()

    @classmethod
    def teardown_class(cls):
        cls.pm.delete_test_directory()

    def setup_method(self):
        self.runner = CliRunner()

    def run_and_verify(self, nb, expected):
        result = self.runner.invoke(run, ['--db-file', self.pm.db_file, nb])
        assert result.exit_code == 0
        assert self.pm.get_output(nb) == expected

    def test_executes(self):
        new_nb = self.pm.add_nb_with_input('2 * 2')
        self.run_and_verify(new_nb, '4')

    def test_executes_multiple(self):
        first_notebook = self.pm.add_nb_with_input('2 * 2')
        second_notebook = self.pm.add_nb_with_input('3 * 3')
        result = self.runner.invoke(run, ['--db-file', self.pm.db_file, first_notebook, second_notebook])
        # Now has been executed
        assert result.exit_code == 0
        assert self.pm.get_output(first_notebook) == '4'
        assert self.pm.get_output(second_notebook) == '9'

    def test_executes_repeatedly(self):
        new_nb = self.pm.add_nb_with_input('2 * 2')
        self.run_and_verify(new_nb, '4')

        # Change input and execute again
        self.pm.set_nb_input(new_nb, '3 * 3')
        self.run_and_verify(new_nb, '9')

    def test_executes_in_git(self):
        # add notebook and commit
        new_nb = self.pm.add_nb_with_input('2 * 2')
        self.pm.commit()
        self.run_and_verify(new_nb, '4')
        #  Changing input but not committing means file is not executed
        self.pm.set_nb_input(new_nb, '3 * 3')
        self.run_and_verify(new_nb, '4')

        # Commit changes, should run
        git_rev = self.pm.commit(new_nb)
        assert git_rev is not None
        self.run_and_verify(new_nb, '9')

    def test_exceptions_in_git(self):
        new_nb = self.pm.add_nb_with_input('Raise ValueError()')
        self.pm.commit()
        # Runs without error, does not save output
        self.run_and_verify(new_nb, '0')

        # Runs again even though it is checked in
        self.pm.set_nb_input(new_nb, '3 * 3')
        self.run_and_verify(new_nb, '9')

        # Won't run again
        self.pm.set_nb_input(new_nb, '4 * 4')
        self.run_and_verify(new_nb, '9')

        # Unless you force it to
        self.runner.invoke(run, ['--db-file', self.pm.db_file, '--force', new_nb])
        assert self.pm.get_output(new_nb) == '16'
