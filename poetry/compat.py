import platform


VENV_BIN_DIR = "Scripts" if platform.system() == "Windows" else "bin"
PYTHON = "python" if platform.system() == "Windows" else "python3"
