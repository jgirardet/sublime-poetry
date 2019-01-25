from collections import defaultdict
import logging
import shutil
import time
import os

import sublime

from ..compat import VENV_BIN_DIR
from ..consts import PACKAGE_NAME
from .helpers import PoetryCommand, Poetry

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryShellCommand(PoetryCommand):
    def is_enabled(self):
        if not super().is_enabled():
            return False

        try:
            from Terminus import terminus  # noqa
        except ImportError:
            return False
        return True

    def is_active(self):
        if not super().is_active():
            return False

        try:
            from Terminus import terminus  # noqa
        except ImportError:
            return False
        return True

    def run(self):
        LOG.debug("Running Poetry Shell Command")
        self.poetry = Poetry(self.window)

        used_venv = self.poetry.used_venv()

        if used_venv is None:
            self.quick_status("No virtualenv installed, aborting")
            return

        activate = "activate"

        if self.poetry.platform != "windows":
            default_shell = os.environ["SHELL"]
            if "fish" in default_shell:
                activate += ".fish"
            if "csh" in default_shell:
                activate += ".csh"

        cmd_line = used_venv / VENV_BIN_DIR / activate

        if self.poetry.platform != "windows":
            cmd_line = ". {}\n".format(str(cmd_line))
        else:
            cmd_line = "{}\n".format(str(cmd_line))

        self.window.run_command(
            "terminus_open", {"config_name": "Default", "panel_name": "Poetry_shell"}
        )
        sublime.set_timeout(
            lambda: self.window.run_command(
                "terminus_send_string", {"string": cmd_line}
            )
        )
