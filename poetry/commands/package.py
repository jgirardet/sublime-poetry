from .helpers import PoetryCommand, Poetry
from ..consts import PACKAGE_NAME
import logging
import re

import sublime_plugin
import sublime

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryAddCommand(PoetryCommand):
    def run(self, custom="", package=None, dev=False):
        dev = "-D" if dev else ""
        cmd_line = "add {}".format(dev)
        if package:
            self.run_poetry_command(cmd_line, package)
        else:
            self.run_input_command(
                "Poetry {}".format(cmd_line), cmd_line, custom=custom
            )


class PoetryRemoveCommand(PoetryCommand):
    def remove_callback(self, id):
        choice = self.packages[id]
        dev = "-D" if "dev" in choice else ""
        package = choice.split()[0]

        self.run_poetry_command("remove", dev, package)

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
            self.run_poetry_command("remove", custom)
        else:
            self.window.show_quick_panel(
                base_normalized + dev_normalized,
                lambda choice: self.remove_callback(choice),
            )


class PoetrySearchCommand(PoetryCommand):
    def write_view(self):
        if not self.runner.poetry.popen.returncode:
            self.result = self.window.new_file()
            self.result.set_scratch(True)
            self.result.set_name("poetry_search_result")
            output = self.runner.output
            results = [i.strip() for i in output.splitlines()]
            self.result.run_command("insert", args={"characters": "\n".join(results)})

    def wait(self):
        if self.runner.is_alive():
            sublime.set_timeout(lambda: self.wait(), 0.2)
        else:
            self.write_view()

    def search(self, name):
        self.run_poetry_command("search -N {}".format(name))
        self.wait()

    def run(self):
        self.poetry = Poetry(self.window)
        self.window.show_input_panel("name", "", lambda x: self.search(x), None, None)


class PoetryAddPackageUnderCursorCommand(sublime_plugin.TextCommand):
    def is_active(self):
        return self.view.name() == "poetry_search_result"

    is_enabled = is_active

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.re_package = re.compile(r"([a-zA-Z0-9\-\_+]+) \(.+\)")

    def run(self, edit):
        line = self.view.substr(self.view.line(self.view.sel()[0]))
        to_find = self.re_package.search(line)
        if to_find:
            package = to_find.group(1)
        else:
            LOG.error("No matching package was found with line %s", line)
            return

        choice = sublime.yes_no_cancel_dialog(
            "Add package  {} to ?".format(package), "dev-dependencies", "dependencies"
        )

        if choice:
            dev = True if choice == 1 else False
            self.view.window().run_command(
                "poetry_add", args={"package": package, "dev": dev}
            )
        else:
            LOG.debug("Add package under cursor cancelled")
