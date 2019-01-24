from fixtures import poetry, PoetryDeferredTestCase
import os

# from pathlib import Path
from unittest.mock import patch, PropertyMock, MagicMock
import tempfile

Poetry = poetry.poetry.Poetry
Path = poetry.utils.Path
PACKAGE_NAME = poetry.consts.PACKAGE_NAME
import toml


class TestEnvUse(PoetryDeferredTestCase):
    def test_run(self):
        p = poetry.commands.PoetryEnvUseCommand(self.window)
        p.run_poetry_command = MagicMock()
        p.envs = ["python2.7", "python3.7", "python3.6 Activated"]

        # already acivated
        choice = "python3.6 Activated"
        p.run(choice)
        self.assertEqual(
            self.view.get_status(PACKAGE_NAME), "python3.6 Activated" + " nothing to do"
        )

        # known but not activated
        choice = "python3.7"
        p.run(choice)
        p.run_poetry_command.assert_called_with("env use", "3.7")

        # unkomw
        choice = "else/where"
        p.run(choice)
        p.run_poetry_command.assert_called_with("env use", "else/where")

    def test_remove(self):
        p = poetry.commands.PoetryEnvRemoveCommand(self.window)
        p.run_poetry_command = MagicMock()

        # already activated
        p.run("python3.6 Activated")
        p.run_poetry_command.assert_called_with("env remove", "python3.6")

        # not  already activated
        p.run("python3.7")
        p.run_poetry_command.assert_called_with("env remove", "python3.7")
