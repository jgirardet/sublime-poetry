import sublime_plugin
from .utils import poetry_used
from collections import defaultdict
from .poetry import Poetry
from .compat import VENV_BIN_DIR


class PoetryCommand(sublime_plugin.WindowCommand):
    def is_active(self):
        return poetry_used(self.window.active_view())

    is_enabled = is_active


class PoetrySetPythonInterpreterCommand(PoetryCommand):
    def run(self):
        self.poetry = Poetry(self.window)
        project = defaultdict(dict)
        project.update(self.window.project_data())
        python_interpreter = self.poetry.venv / VENV_BIN_DIR / "python"

        project["settings"]["python_interpreter"] = str(python_interpreter)
        self.window.set_project_data(project)
