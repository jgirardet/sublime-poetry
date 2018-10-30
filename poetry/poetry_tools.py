import re
from .utils import Path

from .utils import popen_out, get_settings
from .compat import VENV_BIN_DIR
import sublime
import os
from .consts import PACKAGE_NAME
# from .consts import PACKAGE_NAME
import logging

LOG = logging.getLogger(PACKAGE_NAME)


def poetry_cmd():
    """
    Expand ~ and ~user constructions.
    Includes a workaround for http://bugs.python.org/issue14768
    code from sdispatcher/poetry
    """
    poetry_binary_config = get_settings()['poetry_binary']
    if poetry_binary_config:
        poetry_bin = Path(poetry_binary_config)

    else:

        home = os.path.expanduser("~")
        if home.startswith("~/") and home.startswith("//"):
            home = home[1:]

        poetry_bin = Path(home) / ".poetry" / "bin" / "poetry"

    if not poetry_bin.exists():
        raise FileNotFoundError("poetry binary not found")

    LOG.debug('poetry_cmd : %s', poetry_bin)
    return str(poetry_bin)




def get_venv_path():
    out = popen_out([poetry_cmd(), "debug:info"])
    LOG.debug(out.decode())
    venv = (
        re.search(rb"Virtualenv(?:\n.*)* \* (Path:.+)", out)
        .group(1)
        .split(b":")[1]
        .strip()
    )
    LOG.debug("get_venv_path : %s", venv.decode())
    if venv != b"NA":
        python_interpreter = Path(venv.decode()) / VENV_BIN_DIR / "python"
        return python_interpreter

    else:
        return venv.decode()
