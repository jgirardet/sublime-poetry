import logging
import os
import platform
import re
import subprocess

import sublime
import toml

from .consts import PACKAGE_NAME
from .compat import VENV_BIN_DIR, PYTHON_EXEC
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
        # python_exec = "python.exe" if platform.system == "Windows" else "python"

        if self.path.exists():
            cfg = None
            pyvenv = self.path / "pyvenv.cfg"
            # python 3
            if pyvenv.exists():
                cfg = re.search(r"version = (\d.\d.\d)\n", pyvenv.read_text()).group(1)

            # python 2
            else:
                cfg = PythonInterpreter.get_python_version(
                    str(self.path / VENV_BIN_DIR / PYTHON_EXEC)
                )
            LOG.debug(".venv python version  :%s", cfg)
            return cfg

        else:
            return ""

    @classmethod
    def create(cls, path, version, cwd, view=None):
        """Create new .venv according python version

        path : path to interpreter
        version : python version
        cwd: directory (PAth or str)

        Return: Path(new_venv)
        """

        LOG.debug("creating %s", str(cwd))
        if not isinstance(cwd, Path):
            cwd = Path(cwd)

        shell = True if sublime.platform() == "windows" else None

        module = "venv" if version.startswith("3") else "virtualenv"

        # test virtualenv installed
        if version.startswith("2"):
            if subprocess.call([path, "-m", "virtualenv", "--version"], shell=shell):
                LOG.error("virtualenv seems not to be installed")
                raise

        try:
            out = subprocess.check_output(
                [path, "-m", module, ".venv"],
                # "{} -m {} .venv".format(path, module),
                cwd=str(cwd),
                stderr=subprocess.STDOUT,
                # stdout=subprocess.PIPE,
                shell=shell,
                timeout=100,
            )
        except subprocess.TimeoutExpired as err:
            LOG.error(".venv creation: %s", err.output.decode())
            raise err

        except subprocess.CalledProcessError as err:
            LOG.error(".venv creation exited with code %s", err.output.decode())
            raise err

        else:
            LOG.debug(
                ".venv created at %s : %s with message %s",
                str(cwd / ".venv"),
                (cwd / ".venv").exists(),
                out.decode(),
            )
            return cls(cwd=cwd, view=view)
        # LOG.debug('.venv creation return : %s', out.decode())

    def __str__(self):
        return str(self.path)


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

        dirs = {
            "cache": Path(appdirs.user_cache_dir("pypoetry")),
            "config": Path(appdirs.user_config_dir("pypoetry")),
        }

        # pypoetry not alwways create config files
        if not (dirs["config"] / "auth.toml").exists():
            _ = subprocess.call("{} config".format(self.cmd), shell=self.shell)

        return dirs

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

        return self._config

    @property
    def package_version(self):
        return toml.loads(self.pyproject.read_text())['tool']['poetry']['version']
    