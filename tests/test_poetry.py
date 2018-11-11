from unittest import TestCase
from unittest.mock import patch, MagicMock
from fixtures import poetry, create_fake_project
import subprocess
import sublime
import os
import tempfile

Poetry = poetry.poetry.Poetry
Path = poetry.utils.Path


class TestPoetry(TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.poetry = Poetry(self.window)

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command("close_file")

    def test_get_poetry_cmd_no_config(self):
        """return current poetry_binary via recommanded install"""

        self.assertEqual(
            subprocess.check_call(
                [self.poetry.cmd, "--version"], shell=self.poetry.shell
            ),
            0,
        )

    def test_get_poetry_cmd_config(self):
        """return current poetry_binary via config option"""

        self.poetry.config["poetry_binary"] = __file__

        self.assertEqual(self.poetry.get_poetry_cmd(), __file__)

    def test_used_venv(self):
        directory, dirpath, pyproject, venv, project = create_fake_project(venv=True)
        self.poetry.pyproject = pyproject
        if (
            "TRAVIS" in os.environ and os.environ["TRAVIS_OS_NAME"] == "linux"
        ):  # because poetry ignore .venv ifVIRTUAL_ENV set
            new_venv = Path(os.environ["VIRTUAL_ENV"])
        else:
            new_venv = venv

        self.assertEqual(self.poetry.used_venv().resolve(), new_venv.resolve())

    def test_output(self):
        self.poetry.popen = MagicMock()

        self.poetry.output
        self.poetry.popen.stdout.read.assert_called_once_with()

    def test_packages(self):
        file = Path(tempfile.NamedTemporaryFile(delete=False).name)
        tomlfile = '''[tool.poetry.dependencies]
python = "*"
# toml  = "^0.8"
all = "*"
constrant = "^2.1"
[tool.poetry.dev-dependencies]
all = "*"
constrant = "^2.1"'''
        file.write_text(tomlfile)

        p = Poetry(self.window)
        p.pyproject = file

        self.assertEqual(
            p.packages,
            (
                [("all", "*"), ("constrant", "^2.1"), ("python", "*")],
                [("all", "*"), ("constrant", "^2.1")],
            ),
        )
        p.pyproject.unlink()
