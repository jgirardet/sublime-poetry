import logging
import os
import re
import subprocess

import sublime
import toml

from .consts import PACKAGE_NAME
from .utils import Path, startup_info
from .utils import get_settings, find_pyproject, find_root_file
from .interpreters import PythonInterpreter


LOG = logging.getLogger(PACKAGE_NAME)


class Poetry:
    def __init__(self, window):
        self.window = window
        self.view = window.active_view()
        self.config = get_settings(self.view)

        self.cmd = self.get_poetry_cmd()
        self.pyproject = find_pyproject(view=self.view)
        self._cwd = self.pyproject.parent if self.pyproject else None
        self.platform = sublime.platform()
        self.shell = True if self.platform == "windows" else None

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
        LOG.debug("Poetry::run : command = %s", cmd)
        self.popen = subprocess.Popen(
            cmd,
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

    # def check_run(self):

    #     if self.output == None:
    #         return None

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
        if self.platform == "windows":
            regex = rb"Virtualenv(?:\r\r\n.*)* \* (Path:.+)"
        else:
            regex = rb"Virtualenv(?:\n.*)* \* (Path:.+)"

        venv = (re.search(regex, out).group(1).split()[-1].strip()).decode()
        LOG.debug("get_venv_path : %s", venv)
        if venv != b"NA":
            return Path(venv)
        else:
            raise FileNotFoundError("Virtualenv not found")

    @property
    def packages(self):
        content = toml.loads(self.pyproject.read_text())
        base = sorted(content["tool"]["poetry"]["dependencies"].items())
        dev = sorted(content["tool"]["poetry"]["dev-dependencies"].items())
        return base, dev

    @property
    def dot_venv(self):
        return find_root_file(self.view, ".venv")

    @property
    def dot_venv_version(self):

        if self.dot_venv:
            cfg = None
            pyvenv = self.dot_venv / "pyvenv.cfg"
            # python 3
            if pyvenv.exists():
                cfg = re.search(r"version = (\d.\d.\d)\n", pyvenv.read_text()).group(1)

            # python 2
            else:
                cfg = PythonInterpreter.get_python_version(
                    str(self.dot_venv / "bin" / "python")
                )
            LOG.debug("Poetry dot_venv_version :%s", cfg)
            return cfg

        return ""

    def new_dot_venv(self, path, version):
        module = "venv" if version.startswith("3") else "virtualenv"
        p = subprocess.Popen(
            [path, "-m", module, ".venv"],
            # "{} -m {} .venv".format(path, module),
            cwd=self.cwd,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            shell=self.shell,
        )
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired as err:
            LOG.debug("new_dot_venv: %s", err.output)
            return False
        return self._cwd / ".venv"
