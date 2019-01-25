import sublime_plugin

import sublime

from ..consts import (
    PACKAGE_NAME,
    POETRY_STATUS_BAR_TIMEOUT,
    ACTIVE_VERSION,
    CHOICE_SEPARATOR,
)
from ..poetry import Poetry
from ..utils import poetry_used
from .command_runner import PoetryThread, ThreadProgress


class PoetryCommand(sublime_plugin.WindowCommand):
    def is_active(self):
        return poetry_used(self.window.active_view())

    is_enabled = is_active

    def run_poetry_command(
        self, command, *args, show_out=False, end_duration=POETRY_STATUS_BAR_TIMEOUT
    ):
        if not hasattr(self, "poetry"):
            self.poetry = Poetry(self.window)
        self.runner = PoetryThread(command, self.poetry, *args)
        self.runner.start()
        ThreadProgress(self.runner, show_out, end_duration)
        return self.runner

    def run_input_command(self, caption, command, initial="", custom=""):
        def to_run(res):
            self.run_poetry_command(command, res)

        if custom:
            self.run_poetry_command(command, custom)
        else:
            self.window.show_input_panel(
                caption, initial, lambda x: to_run(x), None, None
            )

    def run_after_command(self, fn, sleep):
        """run a  fn after checking after ThreadProgress end"""

        if not hasattr(self, "view"):
            self.view = self.window.active_view()

        def reloader():
            sublime.set_timeout_async(lambda: checker(fn, sleep), sleep)

        def checker(fn, sleep):
            if "succes" in self.view.get_status(PACKAGE_NAME):
                sublime.set_timeout_async(fn, 0)
                return
            if "fail" in self.view.get_status(PACKAGE_NAME):
                return
            reloader()

        reloader()

    # def wait_complete(self, fn):
    #     if self.runner.is_alive():
    #         sublime.set_timeout(lambda: self.wait(), 0.2)
    #     else:
    #         fn()

    def quick_status(self, message, timeout=POETRY_STATUS_BAR_TIMEOUT):
        if not hasattr(self, "view"):
            self.view = self.window.active_view()
        self.view = self.window.active_view()
        self.view.set_status(PACKAGE_NAME, message)
        sublime.set_timeout(lambda: self.view.erase_status(PACKAGE_NAME), timeout)

    def set_sb_version(self, version):
        print("set sb")
        if not hasattr(self, "view"):
            self.view = self.window.active_view()

        self.view.set_status(ACTIVE_VERSION, "Poetry: {}".format(version))


class SimpleListInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, items):
        self.items = items

    def list_items(self):
        return self.items

    def name(self):
        return "choice"

    def validate(self, value):
        if isinstance(value, list):
            return True

        elif not value or value.startswith(CHOICE_SEPARATOR):
            return False
        return True


def titleise(title):
    return " ".join((CHOICE_SEPARATOR, title.strip(), CHOICE_SEPARATOR))
