from unittest import TestCase
from unittest.mock import patch
import sublime
from fixtures import poetry, create_fake_project
from pathlib import Path
import subprocess


class TestPoetry(TestCase):
    def test_poetry_cmd_no_config(self):
        """return current poetry_binary via recommanded install"""

        self.assertEqual(
            subprocess.check_call([poetry.poetry_tools.poetry_cmd(), "--version"]), 0
        )

    def test_poetry_cmd_config(self):
        """return current poetry_binary via config option"""

        with patch.object(
            poetry.poetry_tools,
            "get_settings",
            return_value={"poetry_binary": str(Path(__file__))},
        ) as m:

            self.assertEqual(
                poetry.poetry_tools.poetry_cmd(), str(m()["poetry_binary"])
            )

    def test_get_venv_path(self):
        directory, dirpath, pyproject, venv, project = create_fake_project()

        self.assertEqual(venv, dirpath / ".venv")
