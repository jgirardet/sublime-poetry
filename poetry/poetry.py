import logging
import os
import re
import subprocess

import sublime

from .consts import PACKAGE_NAME
from .utils import Path, startup_info
from .utils import get_settings, find_pyproject


LOG = logging.getLogger(PACKAGE_NAME)


class Poetry:
    def __init__(self, window):
        self.window = window
        self.view = window.active_view()
        self.config = get_settings(self.view)

        self.cmd = self.get_poetry_cmd()
        self.pyproject = find_pyproject(view=self.view)
        self._cwd = self.pyproject.parent if self.pyproject else None

        self.shell = True if sublime.platform() == "windows" else None

        self._output = None

    @property
    def cwd(self):
        if self._cwd:
            return str(self._cwd)

    def get_poetry_cmd(self):
        """
        Expand ~ and ~user constructions.
        Includes a workaround for http://bugs.python.org/issue14768
        code from sdispatcher/poetry
        """
        if self.config["poetry_binary"]:
            poetry_bin = Path(self.config["poetry_binary"])

        else:

            home = os.path.expanduser("~")
            if home.startswith("~/") and home.startswith("//"):
                home = home[1:]

            poetry_bin = Path(home) / ".poetry" / "bin" / "poetry"

        if not poetry_bin.exists():
            raise FileNotFoundError("poetry binary not found")

        LOG.debug("poetry_cmd : %s", poetry_bin)
        return str(poetry_bin)

    def run(self, command):
        """run a poetry command in current directory"""
        cmd = command.split()
        cmd.insert(0, self.cmd)
        self.popen = subprocess.Popen(
            cmd,
            startupinfo=startup_info(),
            cwd=self.cwd,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            shell=self.shell,
        )

    @property
    def poll(self):
        return self.popen.poll()

    @property
    def output(self):
        if self._output is None:
            self._output = self.popen.stdout.read()
        return self._output

    def check_run(self):

        if self.output == None:
            return None

        # except subprocess.CalledProcessError as err:
        #     LOG.error(
        #         "Poetry run for command %s failed with return_code %d and the following output:\n%s",
        #         err.cmd,
        #         err.returncode,
        #         err.output.decode(),
        #     )
        #     LOG.debug("Poetry vars at fail: %s", vars(self))
        #     raise
        # else:
        #     LOG.debug('output of command "%s" : %s', command, output.decode())
        #     return output

    @property
    def venv(self):
        self.run("debug:info")
        out = self.output
        venv = (
            re.search(rb"Virtualenv(?:\n.*)* \* (Path:.+)", out)
            .group(1)
            .split(b":")[1]
            .strip()
        ).decode()
        LOG.debug("get_venv_path : %s", venv)
        if venv != b"NA":
            return Path(venv)
        else:
            raise FileNotFoundError("Virtualenv not found")
