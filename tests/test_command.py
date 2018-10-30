from unittest import TestCase

from fixtures import poetry, PoetryTestCase
import sublime
import os
from pathlib import Path


class TestPoetry(PoetryTestCase):
    def test_poetry_package_name(self):
        self.assertEqual(poetry.PACKAGE_NAME, "poetry")

    # def test_open(self):

    def test_set_python_interpreter(self):
        self.create_venv()
        self.window.run_command("poetry_set_python_interpreter")
        project_data = self.window.project_data()

        if "CI" in os.environ:  # because poetry ignore .venv ifVIRTUAL_ENV set
            base = Path(os.environ["VIRTUAL_ENV"])
        else:
            base = self.venv
        self.assertEqual(
            project_data,
            {
                "settings": {"python_interpreter": str(base / "bin" / "python")},
                "folders": [{"path": self.dir.name}],
            },
        )
