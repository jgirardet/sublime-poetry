import re
from .utils import Path

from .utils import popen_out
from .compat import VENV_BIN_DIR
import sublime
import os


def poetry_cmd():
    """
    Expand ~ and ~user constructions.
    Includes a workaround for http://bugs.python.org/issue14768
    code from sdispatcher/poetry
    """
    home = os.path.expanduser("~")
    if home.startswith("~/") and home.startswith("//"):
        home = home[1:]

    poetry_bin = str(Path(home) / ".poetry" / "bin" / "poetry")

    try:
        popen_out([poetry_bin], cwd=None)
    except FileNotFoundError:
        return False

    return poetry_bin


POETRY_CMD = poetry_cmd()


def get_venv_path():
    out = popen_out([POETRY_CMD, "debug:info"])
    venv = (
        re.search(rb"Virtualenv(?:\n.*)* \* (Path:.+)", out)
        .group(1)
        .split(b":")[1]
        .strip()
    )
    if venv and venv != b"NA":
        python_interpreter = Path(venv.decode()) / VENV_BIN_DIR / "python"
        return python_interpreter
