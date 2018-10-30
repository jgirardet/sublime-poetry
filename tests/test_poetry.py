from unittest import TestCase
from unittest.mock import patch
from fixtures import poetry, create_fake_project
from pathlib import Path
import subprocess
import sublime

Poetry = poetry.poetry.Poetry

window = sublime.active_window()


class TestPoetry(TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.poetry = Poetry(self.window)

    def test_get_poetry_cmd_no_config(self):
        """return current poetry_binary via recommanded install"""

        self.assertEqual(subprocess.check_call([self.poetry.cmd, "--version"]), 0)

    def test_get_poetry_cmd_config(self):
        """return current poetry_binary via config option"""

        self.poetry.config["poetry_binary"] = __file__

        self.assertEqual(self.poetry.get_poetry_cmd(), __file__)

    def test_venv(self):
        directory, dirpath, pyproject, venv, project = create_fake_project()
        self.poetry._cwd = dirpath
        self.assertEqual(self.poetry.venv, dirpath / ".venv")
