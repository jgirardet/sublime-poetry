import logging
import os
import re
import subprocess

import sublime
import toml

from .consts import PACKAGE_NAME
from .utils import Path, startup_info
from .utils import get_settings, find_pyproject, find_root_file, import_module_from_path
from .interpreters import PythonInterpreter


LOG = logging.getLogger(PACKAGE_NAME)


class Venv:
    """
    Class managing the .venv path inside poetry, projects
    """

    def __init__(self, view=None, cwd=None):

        if cwd is not None:
            self.cwd = cwd if isinstance(cwd, Path) else Path(cwd)
        else:
            self.cwd = None

        self.view = view if view else sublime.active_window().active_view()

    def exists(self):
        return bool(self.path.exists())

    @property
    def path(self):
        if not self.cwd:
            return find_root_file(self.view, ".venv")
        return self.cwd / ".venv"

    @property
    def version(self):
        """python version

        str(mja min micro)
        """

        if self:
            cfg = None
            pyvenv = self.path / "pyvenv.cfg"
            # python 3
            if pyvenv.exists():
                cfg = re.search(r"version = (\d.\d.\d)\n", pyvenv.read_text()).group(1)

            # python 2
            else:
                cfg = PythonInterpreter.get_python_version(
                    str(self.path / "bin" / "python")
                )
            LOG.debug(".venv python version  :%s", cfg)
            return cfg

        return ""

    @classmethod
    def create(cls, path, version, cwd, view=None):
        """Create new .venv according python version

        path : path to interpreter
        version : python version
        cwd: directory (PAth or str)

        Return: Path(new_venv)
        """

        if not isinstance(cwd, Path):
            cwd = Path(cwd)

        shell = True if sublime.platform() == "windows" else None

        module = "venv" if version.startswith("3") else "virtualenv"
        p = subprocess.Popen(
            [path, "-m", module, ".venv"],
            # "{} -m {} .venv".format(path, module),
            cwd=str(cwd),
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            shell=shell,
        )
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired as err:
            LOG.debug("new_dot_venv: %s", err.output)
            return False
        return cls(cwd=cwd, view=view)


class Poetry:
    def __init__(self, window, cwd=None):
        self.window = window
        self.view = window.active_view()
        self.settings = get_settings(self.view)

        self.pyproject = find_pyproject(view=self.view)
        self._cwd = cwd

        self.cmd = self.get_poetry_cmd()

        self._venv = None

        self.platform = sublime.platform()
        self.shell = True if self.platform == "windows" else None

    @property
    def venv(self):
        if not self._venv:
            return Venv(self.view, self.cwd)
        return self._venv

    @property
    def cwd(self):
        if self._cwd:
            return Path(self._cwd)
        return self.pyproject.parent

    def used_venv(self):
        self.run("debug:info")
        out = self.output
        LOG.debug("used_venv_out : %s", out)
        if self.platform == "windows":
            regex = rb"Virtualenv(?:\r\r\n.*)* \* (Path:.+)"
        else:
            regex = rb"Virtualenv(?:\n.*)* \* (Path:.+)"

        venv = (re.search(regex, out).group(1).split()[-1].strip()).decode()
        LOG.debug("get_venv_path : %s", venv)
        if venv != b"NA":
            return Path(venv)
        else:
            return None

    def get_poetry_cmd(self):
        """
        Expand ~ and ~user constructions.
        Includes a workaround for http://bugs.python.org/issue14768
        code from sdispatcher/poetry
        """
        if self.settings["poetry_binary"]:
            print("using poetry binary")
            poetry_bin = Path(self.settings["poetry_binary"])

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
            cwd=str(self.cwd),
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            shell=self.shell,
        )

    @property
    def poetry_root(self):
        return Path(self.cmd).parents[1]

    @property
    def poll(self):
        return self.popen.poll()

    @property
    def output(self):
        return self.popen.stdout.read()

    @property
    def packages(self):
        content = toml.loads(self.pyproject.read_text())
        base = sorted(content["tool"]["poetry"]["dependencies"].items())
        dev = sorted(content["tool"]["poetry"]["dev-dependencies"].items())
        return base, dev

    def appdirs(self):
        appdirs = import_module_from_path(
            "appdirs", str(self.poetry_root / "lib" / "poetry" / "utils" / "appdirs.py")
        )

        return {
            "cache": Path(appdirs.user_cache_dir("pypoetry")),
            "config": Path(appdirs.user_config_dir("pypoetry")),
        }

    @property
    def auth(self):
        # if not self._config:
        config_dir = self.appdirs()["config"]
        auth = toml.loads((config_dir / "auth.toml").read_text())

        return auth

    @property
    def config(self):
        # if not self._config:
        self.run("config --list")
        self._config = toml.loads(self.output.decode())

        # long = []

        # for cle in self._config:
        #     for sous_cle in self._config[cle]:
        #         for ss_cle in  self._config[cle][sous_cle]:
        #             long.append((cle, sous_cle, ss_cle))

        # for file in ["auth.toml", "config.toml"]:
        #     self._config.update(toml.loads((config_dir / file).read_text()))

        return self._config
