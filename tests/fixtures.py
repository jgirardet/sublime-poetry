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
    def setUp(self):

        #sublime :
        self.window = sublime.active_window()
        self.view = self.window.new_file()

        #setup test directory
        self.dir = tempfile.TemporaryDirectory()
        self.dirpath = Path(self.dir.name)
        self.toml = self.dirpath / "pyproject.toml"
        self.env = self.dirpath / ".venv"

        self.create_env()

        self.project = self.dirpath / "bla.sublime-project"
        

        self.old_data = self.window.project_data()

        
        self.init_project()

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command("close_file")

        self.window.set_project_data(self.old_data)


    def create_env(self):
        self.check_call([poem.compat.PYTHON, "-m", "venv", ".venv"])
    

    def popen(self, *args, **kwargs):
        return subprocess.Popen(
            *args, cwd=str(self.dirpath), startupinfo=poem.utils.startup_info(), **kwargs
        )

    def check_call(self, *args, **kwargs):
        return subprocess.check_call(
            *args, cwd=self.dir.name, startupinfo=poem.utils.startup_info(), **kwargs
        )

    def init_project(self):
        self.project.write_text(PROJECT.format(self.dir.name))
        self.window.set_project_data({"folders": [{"path": str(self.dirpath)}]})
        self.toml.write_text(BLANK)
