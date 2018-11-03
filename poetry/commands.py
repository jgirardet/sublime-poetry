from collections import defaultdict
import logging
from queue import Queue

import sublime_plugin

from .poetry import Poetry
from .compat import VENV_BIN_DIR
from .utils import poetry_used, timed
from .consts import PACKAGE_NAME
from .command_runner import PoetryThread, ThreadProgress

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryCommand(sublime_plugin.WindowCommand):
    def is_active(self):
        return poetry_used(self.window.active_view())

    is_enabled = is_active

    def init_command(self):
        self.poetry = Poetry(self.window)
        self.output = Queue(maxsize=1)


class PoetrySetPythonInterpreterCommand(PoetryCommand):
    def run(self):
        self.init_command()
        project = defaultdict(dict)
        project.update(self.window.project_data())
        python_interpreter = self.poetry.venv / VENV_BIN_DIR / "python"

        project["settings"]["python_interpreter"] = str(python_interpreter)
        self.window.set_project_data(project)


class PoetryInstallCommand(PoetryCommand):
    def run(self):
        self.init_command()
        runner = PoetryThread("install", self.poetry, self.output)
        runner.start()
        ThreadProgress(runner, "installed")


class PoetryInstallNoDevCommand(PoetryCommand):
    @timed
    def run(self):
        self.init_command()
        runner = PoetryThread("install --no-devd", self.poetry, self.output)
        runner.start()
        ThreadProgress(runner, "installed No dev")
