from collections import defaultdict
import logging
import shutil

import sublime_plugin
import sublime

from .poetry import Poetry
from .compat import VENV_BIN_DIR
from .utils import poetry_used, timed
from .consts import PACKAGE_NAME
from .interpreters import PythonInterpreter
from .command_runner import PoetryThread, ThreadProgress

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryCommand(sublime_plugin.WindowCommand):
    def is_active(self):
        return poetry_used(self.window.active_view())

    is_enabled = is_active

    def run_command(self, command, *args):
        self.poetry = Poetry(self.window)
        runner = PoetryThread(command, self.poetry, *args)
        runner.start()
        ThreadProgress(runner)

    def run_input_command(self, caption, command, custom=""):
        if custom:
            self.run_command(command, custom)
        else:
            self.window.show_input_panel(
                caption, "", lambda x: self.run_command(command, x), None, None
            )


class PoetrySetPythonInterpreterCommand(PoetryCommand):
    def run(self):
        sublime.set_timeout_async(self._run, 0)

    def _run(self):
        self.poetry = Poetry(self.window)
        project = defaultdict(dict)
        project.update(self.window.project_data())
        python_interpreter = self.poetry.venv / VENV_BIN_DIR / "python"

        project["settings"]["python_interpreter"] = str(python_interpreter)

        self.window.set_project_data(project)


class PoetryInstallCommand(PoetryCommand):
    def run(self):
        self.run_command("install")


class PoetryInstallNoDevCommand(PoetryCommand):
    def run(self):
        self.run_command("install --no-dev")


class PoetryUpdateCommand(PoetryCommand):
    def run(self):
        self.run_command("update")


class PoetryAddCommand(PoetryCommand):
    def run(self, custom=""):
        self.run_input_command("Poetry add", "add", custom)


class PoetryAddDevCommand(PoetryCommand):
    def run(self, custom=""):
        self.run_input_command("Poetry add", "add -D", custom)


class PoetryRemoveCommand(PoetryCommand):
    def remove_callback(self, id):
        choice = self.packages[id]
        dev = "-D" if "dev" in choice else ""
        package = choice.split()[0]

        self.run_command("remove", dev, package)

    def run(self, custom=""):
        self.poetry = Poetry(self.window)
        base, dev = self.poetry.packages
        dev_normalized = [
            " ".join((name, "   ", str(version), "  **dev** ")) for name, version in dev
        ]
        base_normalized = [
            " ".join((name, "   ", str(version)))
            for name, version in base
            if name != "python"
        ]

        self.packages = base_normalized + dev_normalized

        if custom:
            self.run_command("remove", custom)
        else:
            self.window.show_quick_panel(
                base_normalized + dev_normalized,
                lambda choice: self.remove_callback(choice),
            )


class PoetryInstallInVenvCommand(PoetryCommand):
    def create_and_install(self, path, version):
        if self.poetry.new_dot_venv(path, version):
            self.window.run_command("poetry_install")

    def callback(self, id):
        path, version = self.python_interpreter.execs_and_pyenv[id]
        LOG.debug("using %s", path)
        if version == self.poetry.dot_venv_version:
            go_on = sublime.ok_cancel_dialog(
                ".venv is already with version {}. Continue ?".format(version)
            )
            if not go_on:
                LOG.debug("Install command interupted by user")
                return

        if self.poetry.venv.exists():
            shutil.rmtree(str(self.poetry.venv))

        sublime.set_timeout_async(lambda: self.create_and_install(path, version), 0)

    def run(self):
        self.poetry = Poetry(self.window)
        self.interpreters = []
        self.python_interpreter = PythonInterpreter()
        for i in self.python_interpreter.execs_and_pyenv:
            self.interpreters.append("{}  {}".format(*i))

        self.window.show_quick_panel(
            self.interpreters, lambda choice: self.callback(choice)
        )
