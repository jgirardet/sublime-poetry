import sys
from unittest import TestCase
import tempfile
import subprocess
import sublime

poem = sys.modules["poem.poem"]
Path = poem.utils.Path

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
}}
"""


class PoemTestCase(TestCase):
    # @classmethod
    # def setUpClass(cls):
    #     window = sublime.active_window()
    #     window.run_command("new_window")
    #     cls.dir = tempfile.TemporaryDirectory()

    #     cls.window = sublime.active_window()
    #     cls.window.set_project_data({"folders": [{"path": cls.dir.name}]})

    #     cls.path = Path(cls.dir.name)
    #     cls.pyproject = cls.path / "pyproject.toml"

    #     cls.create_env()


    #     cls.pyproject.touch()
    #     cls.pyproject.write_text(BLANK)

    # @classmethod
    # def tearDownClass(cls):
    #     import time

    #     cls.window.run_command("close_window")


    @classmethod
    def create_env(cls):
        cls.check_call([poem.compat.PYTHON, "-m", "venv", ".venv"])

    def popen(self, *args, **kwargs):
        return subprocess.Popen(
            *args, cwd=str(self.path), startupinfo=poem.utils.startup_info(), **kwargs
        )

    @classmethod
    def check_call(cls, *args, **kwargs):
        return subprocess.check_call(
            *args, cwd=cls.dir.name, startupinfo=poem.utils.startup_info(), **kwargs
        )
