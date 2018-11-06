import sys
from unittest import TestCase
import tempfile
import subprocess
import sublime
from unittesting import DeferrableTestCase
import shutil

poetry = sys.modules["poetry.poetry"]
Path = poetry.utils.Path

BLANK = """[tool.poetry]
name = "rien"
version = "0.1.0"
description = ""
authors = ["Jimmy Girardet <ijkl@netc.fr>"]

[tool.poetry.dependencies]
python = "*"
# toml  = "^0.8"

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
    pyproject = dirpath / "pyproject.toml"
    venv_path = dirpath / ".venv"
    project = dirpath / "bla.sublime-project"
    project.write_text(PROJECT.format(directory.name))
    pyproject.write_text(BLANK)
    (dirpath / ".gitignore").write_text(".venv/")

    if venv:
        subprocess.check_call(
            # [poetry.compat.PYTHON, "-m", "venv", ".venv"],
            # ["/usr/bin/python3.7", "-m", "venv", ".venv"],
            "{} -m venv .venv".format(poetry.compat.PYTHON),
            cwd=str(dirpath),
            startupinfo=poetry.utils.startup_info(),
            shell=True,
        )
    return directory, dirpath, pyproject, venv_path, project


class PoetryTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # sublime :
        window = sublime.active_window()
        window.run_command("new_window")
        cls.window = sublime.active_window()
        cls.view = cls.window.new_file()

        # project
        directory, dirpath, pyproject, venv, project = create_fake_project(venv=True)
        cls.dir = directory
        cls.dirpath = dirpath
        cls.pyproject = pyproject
        cls.venv = venv
        cls.project = project

        cls.window.set_project_data({"folders": [{"path": str(cls.dirpath)}]})

    @classmethod
    def tearDownClass(cls):
        if cls.view:
            cls.view.set_scratch(True)
            cls.view.window().focus_view(cls.view)
            cls.view.window().run_command("close_file")

        cls.window.run_command("close_window")

        cls.dir.cleanup()

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


class PoetryDeferredTestCase(DeferrableTestCase):
    @classmethod
    def setUpClass(cls):
        # sublime :
        window = sublime.active_window()
        window.run_command("new_window")
        cls.window = sublime.active_window()
        cls.view = cls.window.new_file()

        # project
        directory, dirpath, pyproject, venv, project = create_fake_project(venv=True)
        cls.dir = directory
        cls.dirpath = dirpath
        cls.pyproject = pyproject
        cls.venv = venv
        cls.project = project

        cls.window.set_project_data({"folders": [{"path": str(cls.dirpath)}]})

    @classmethod
    def tearDownClass(cls):
        if cls.view:
            cls.view.set_scratch(True)
            cls.view.window().focus_view(cls.view)
            cls.view.window().run_command("close_file")

        cls.window.run_command("close_window")

        shutil.rmtree(cls.dir.name, ignore_errors=True)
        # cls.dir.cleanup()

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
