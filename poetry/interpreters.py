import itertools
import re
import subprocess
import os

from pathlib import Path


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

        return self._build

    @property
    def versions(self):
        """All environment (base + virtualenv) installed.

        Return: set(Path)
        """
        if not self._versions:
            self._versions = self.as_dict(self.versions_path.glob("*"))

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

    def get_python_version(self, python_executable):
        """Get exact python version"""

        # formatting since print tupple is different for python2 and 3
        find_version = "{} -c \"import sys;print('%s.%s.%s' % (sys.version_info.major ,sys.version_info.minor, sys.version_info.micro))\"".format(
            python_executable
        )

        try:
            version_out = subprocess.check_output(
                find_version, shell=True, executable=self.default_shell
            )
        except FileNotFoundError:
            # LOG.debug("is_python3_executable : FileNotFoundError")
            return False

        except subprocess.CalledProcessError as err:
            # LOG.debug("is_python3_executable : CalledProcessError %s", err)
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
        return system_paths

    def _execs(self):
        binaries = set()
        execs = {}
        for path in self.system_paths:
            # print(path)
            if path.endswith(".pyenv/bin"):
                self._pyenv_path = Path(path).parent
                continue
            elif ".pyenv" in path:
                pass
            else:
                path = Path(path)
                binaries.update((p.resolve() for p in path.glob("python*")))

        for e in sorted(binaries):
            if re.search(r"python\d?\.?\d?$", str(e)):
                execs[str(e)] = self.get_python_version(str(e))

        return execs

    def _pyenv(self):
        if not self._pyenv_path:
            self.execs
        if not self._pyenv_path:
            return

        return Pyenv(self._pyenv_path)


    def _execs_and_pyenv(self):
        if self.pyenv:
            return itertools.chain(self.execs, self.pyenv.base_env)

        else:
            self.execs


# if __name__ == "__main__":
# bp = PythonInterpreter()
# bp.execs    #
# print(bp.execs_and_pyenv)
# import sublime
# sublime.show_quick_menu(bp.execs_and_pyenv, lambda x: x)
# p = Pyenv("/home/jimmy/.pyenv")
# print("\nvenv", p.venv)
# print("\nbase", p.base_env)
# print("\nversio", p.versions)
# print('\nbiuld', p.build)
