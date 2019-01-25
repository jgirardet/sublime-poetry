from .helpers import Poetry, PoetryCommand, titleise, SimpleListInputHandler
import sublime
import sublime_plugin
from collections import defaultdict
from ..compat import VENV_BIN_DIR
from ..interpreters import PythonInterpreter
from .command_runner import ThreadProgress, PoetryThread


class PoetrySetPythonInterpreterCommand(PoetryCommand):
    def run(self):
        self.poetry = Poetry(self.window)
        sublime.set_timeout_async(self._run, 0)

    def _run(self):
        venv = self.poetry.used_venv()
        project = defaultdict(dict)
        project.update(self.window.project_data())
        prefix = ""

        if not venv:
            self.quick_status("Python Interpreter could not be set")
            if "python_interpreter" in project["settings"]:
                del project["settings"]["python_interpreter"]
            prefix = "No "

        else:
            python_interpreter = venv / VENV_BIN_DIR / "python"
            project["settings"]["python_interpreter"] = str(python_interpreter)

        self.window.set_project_data(project)
        self.quick_status(prefix + "python interpreter set")


class PoetryInstallCommand(PoetryCommand):
    def run(self):
        self.run_poetry_command("install")


class PoetryInstallNoDevCommand(PoetryCommand):
    def run(self):
        self.run_poetry_command("install --no-dev")


class PoetryUpdateCommand(PoetryCommand):
    def run(self):
        self.run_poetry_command("update")


class PoetryEnvUseCommand(PoetryCommand):
    def run(self, choice):

        if choice in self.envs:
            # already know interpreters
            if "Activated" in choice:
                self.quick_status(choice + " nothing to do")
                return
            else:
                self.run_poetry_command("env use", choice[-3:])
        else:
            # not known interpreters
            self.run_poetry_command("env use", choice)

        self.run_after_command(
            lambda: self.window.run_command("poetry_set_python_interpreter"), 50
        )

    @property
    def all_envs(self):
        # poetry known envs
        self.envs = self.poetry.env_list

        # systems envs
        interpreters = []
        python_interpreter = PythonInterpreter()
        interpreters = [
            interpreter[0] for interpreter in python_interpreter.execs_and_pyenv
        ]

        # merge
        return (
            [titleise("available envs")]
            + self.envs
            + ["", titleise("available interpereters")]
            + interpreters
        )

    def input(self, args):
        self.poetry = Poetry(self.window)
        return SimpleListInputHandler(self.all_envs)


class PoetryEnvRemoveCommand(PoetryCommand):
    def run(self, choice):
        env = choice.split()[0]
        self.run_poetry_command("env remove", env)
        self.run_after_command(
            lambda: self.window.run_command("poetry_set_python_interpreter"), 100
        )

    def input(self, args):
        self.poetry = Poetry(self.window)
        envs = self.poetry.env_list
        if not envs:
            envs = [titleise("nothing to do")]
        return SimpleListInputHandler(envs)


class PoetryInitCommand(sublime_plugin.WindowCommand):
    def run(self):
        poetry = Poetry(self.window)
        runner = PoetryThread("init -n", poetry)
        runner.start()
        ThreadProgress(runner)
