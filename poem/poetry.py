import re
from .utils import Path

from .utils import popen_out
from .compat import VENV_BIN_DIR


def get_venv_path():
    out = popen_out(["poetry", "debug:info"])
    venv = (
        re.search(rb"Virtualenv(?:\n.*)* \* (Path:.+)", out)
        .group(1)
        .split(b":")[1]
        .strip()
    )
    if venv and venv != b"NA":
        python_interpreter = Path(venv.decode()) / VENV_BIN_DIR / "python"
        return python_interpreter
