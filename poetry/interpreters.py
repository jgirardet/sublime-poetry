import itertools
from collections import OrderedDict
import logging
import re
import subprocess
import os

from .consts import PACKAGE_NAME
from .utils import Path

LOG = logging.getLogger(PACKAGE_NAME)


class Pyenv:
    def __init__(self, path):

        # self.path = Path(path) if not isinstance(path, Path) else path
        self.path = path

        self._build = None
        self._versions = None
        self._base_env = None
        self._venv = None
        self.versions_path = self.path / "versions"
        self.build_path = (
            self.path / "plugins" / "python-build" / "share" / "python-build"
        )

    @property
    def build(self):
        """All installable environment via pyenv

        Return: set(Path)
        """

        def as_dict():
            return self.as_dict("build")

        if not self._build:
            self._build = self.as_dict(self.build_path.glob("*"))
            self._build.pop("patches")
            # LOG.debug("Pyenv build %s", self._build)

        return self._build

    @property
    def versions(self):
        """All environment (base + virtualenv) installed.

        Return: set(Path)
        """
        if not self._versions:
            self._versions = self.as_dict(self.versions_path.glob("*"))
            LOG.debug("Pyenv versions %s", self._versions)
        return self._versions

    @property
    def base_env(self):
        """All pyenv environment installed

        Return: dict(bin:version)
        """
        if not self._base_env:
            self._base_env = {
                str(v / "bin" / "python"): k
                for k, v in self.versions.items()
                if k in self.build
            }
            LOG.debug("Peynv base_env : %s", self._base_env)

        return self._base_env

    @property
    def venv(self):
        """All pyenv virtualenv installed

        Return: dict(bin:version)
        """
        if not self._venv:
            self._venv = {
                str(v / "bin" / "python"): k
                for k, v in self.versions.items()
                if k not in self.build
            }

            LOG.debug("Peynv base_env : %s", self._venv)
        return self._venv

    @staticmethod
    def as_dict(groupe):
        return {v.name: v for v in sorted(groupe)}


class PythonInterpreter:
    def __init__(self):
        # if platform.system() != "Windows":
        self.default_shell = os.environ.get("SHELL", "/bin/bash")
        self.system_paths = self._system_paths()
        self._pyenv_path = None

        self.execs = self._execs()
        self.pyenv = self._pyenv()
        self.execs_and_pyenv = self._execs_and_pyenv()

    @staticmethod
    def get_python_version(python_executable, default_shell=None):
        """Get exact python version

        return: str(major minor micro)
        """

        # formatting since print tupple is different for python2 and 3
        find_version = "{} -c \"import sys;print('%s.%s.%s' % (sys.version_info.major ,sys.version_info.minor, sys.version_info.micro))\"".format(
            python_executable
        )

        try:
            version_out = subprocess.check_output(
                find_version, shell=True, executable=default_shell
            )
        except FileNotFoundError:
            LOG.debug("get_python_version : FileNotFoundError")
            return False

        except subprocess.CalledProcessError as err:
            LOG.debug("get_python_version: CalledProcessError %s", err)
            return False

        else:
            return version_out.decode().strip()

    def _system_paths(self):
        system_paths = (
            re.search(
                r"(?m)^PATH=(.*)",
                subprocess.check_output([self.default_shell, "-ic", "env"]).decode(),
            )
            .group(1)
            .split(":")
        )
        LOG.debug("PythonInterpreter system_paths: %s", system_paths)
        return system_paths

    def _execs(self):
        binaries = set()
        execs = {}
        for path in self.system_paths:
            # print(path)
            if path.endswith("pyenv/bin") or path.endswith("pyenv/shims") :
                self._pyenv_path = Path(path).parent
                continue
            elif ".pyenv" in path:
                pass
            else:
                path = Path(path)
                binaries.update((p.resolve() for p in path.glob("python*")))

        for e in sorted(binaries):
            if re.search(r"python\d?\.?\d?$", str(e)):
                LOG.debug('_execs tested: %s', str(e))
                execs[str(e)] = self.get_python_version(str(e), self.default_shell)

        LOG.debug("PythonInterpreter exec: %s", execs)
        return execs

    def _pyenv(self):
        if not self._pyenv_path:
            self.execs
        if not self._pyenv_path:
            return

        return Pyenv(self._pyenv_path)

    def _execs_and_pyenv(self):
        if self.pyenv:
            duo = dict(self.execs)
            duo.update(self.pyenv.base_env)
            res = tuple(sorted(duo.items(), key=lambda t: t[0]))
            LOG.debug("PythonInterpreter exces and pyenv : %s", res)
            return res

        else:
            self.execs
