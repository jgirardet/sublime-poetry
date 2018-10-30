import sublime_plugin
from .utils import get_settings, poetry_used
from collections import defaultdict
from .poetry_tools import get_venv_path

class PoetrySetPythonInterpreterCommand(sublime_plugin.WindowCommand):
    def is_active(self):
        return poetry_used(self.window.active_view())

    is_enabled = is_active

    def run(self):
        config = get_settings(self.window.active_view())
        if config["poetry_autoset_path"]:

            project = defaultdict(dict)
            project.update(self.window.project_data())
            project["settings"]["python_interpreter"] = str(get_venv_path())
            self.window.set_project_data(project)
