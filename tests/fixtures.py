import sys
from unittest import TestCase
import tempfile
import subprocess

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
    def setUp(self):

        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name)
        self.toml = self.path / "pyproject.toml"
        self.env = self.path / ".env"

        self.create_env()

        self.project = self.path / "bla.sublime-project"
        self.init_project()

    def create_env(self):
        self.check_call([poem.compat.PYTHON, "-m", "venv", ".env"])

    # def tearDown(self):
    #     import time
    #     time.sleep(15)

    def popen(self, *args, **kwargs):
        return subprocess.Popen(
            *args, cwd=str(self.path), startupinfo=poem.utils.startup_info(), **kwargs
        )

    def check_call(self, *args, **kwargs):
        return subprocess.check_call(
            *args, cwd=self.dir.name, startupinfo=poem.utils.startup_info(), **kwargs
        )

    def init_project(self):
        self.project.write_text(PROJECT.format(self.dir.name))
