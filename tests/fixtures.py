import sys
from unittest import TestCase
import tempfile
import subprocess
import sublime
import os


poetry = sys.modules["poetry.poetry"]
Path = poetry.utils.Path

BLANK = """[tool.poetry]
name = "rien"
version = "0.1.0"
description = ""
authors = ["Jimmy Girardet <ijkl@netc.fr>"]

[tool.poetry.dependencies]
python = "*"

[tool.poetry.dev-dependencies]"""


PROJECT = """{{
    "folders":
    [
        {{
                    "path": "."
        }}
    ],
}}"""


def create_fake_project(venv=False):
    directory = tempfile.TemporaryDirectory()
    dirpath = Path(directory.name)
    toml = dirpath / "pyproject.toml"
    venv = dirpath / ".venv"
    project = dirpath / "bla.sublime-project"

    if venv:
        subprocess.check_call(
            [poetry.compat.PYTHON, "-m", "venv", ".venv"],
            cwd=str(dirpath),
            startupinfo=poetry.utils.startup_info(),
        )
    return directory, dirpath, toml, venv, project


class PoetryTestCase(TestCase):
    def setUp(self):
        # sublime :
        window = sublime.active_window()
        window.run_command("new_window")
        self.window = sublime.active_window()
        self.view = self.window.new_file()

        # setup test directory
        self.dir = tempfile.TemporaryDirectory()
        self.dirpath = Path(self.dir.name)
        self.toml = self.dirpath / "pyproject.toml"
        self.env = self.dirpath / ".venv"

        self.project = self.dirpath / "bla.sublime-project"

        # self.old_data = self.window.project_data()

        self.init_project()

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command("close_file")

        self.window.run_command("close_window")

        self.dir.cleanup()

        # self.window.set_project_data(self.old_data)

    def create_venv(self):
        self.check_call([poetry.compat.PYTHON, "-m", "venv", ".venv"])

    def popen(self, *args, **kwargs):
        return subprocess.Popen(
            *args,
            cwd=str(self.dirpath),
            startupinfo=poetry.utils.startup_info(),
            **kwargs
        )

    def check_call(self, *args, **kwargs):
        return subprocess.check_call(
            *args,
            cwd=str(self.dirpath),
            startupinfo=poetry.utils.startup_info(),
            **kwargs
        )

    def init_project(self):
        self.project.write_text(PROJECT.format(self.dir.name))
        self.window.set_project_data({"folders": [{"path": str(self.dirpath)}]})
        self.toml.write_text(BLANK)
