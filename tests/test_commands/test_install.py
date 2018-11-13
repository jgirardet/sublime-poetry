from fixtures import PoetryDeferredTestCase, poetry
import shutil
from unittest.mock import patch


class TestInstallCommands(PoetryDeferredTestCase):
    def setUp(self):
        super().setUp()
        if (self.dirpath / "poetry.lock").exists():
            (self.dirpath / "poetry.lock").unlink()

    def test_install(self):

        self.assertTrue((self.dirpath / ".venv").exists())
        self.window.run_command("poetry_install")
        yield self.status
        self.assertEqual(self.result, True)

    def test_install_no_dev(self):
        self.window.run_command("poetry_install_no_dev")

        yield self.status

        self.assertTrue((self.dirpath / "poetry.lock").exists())
        self.assertEqual(self.result, True)

    def test_update(self):
        self.window.run_command("poetry_update")
        yield self.status
        self.assertTrue((self.dirpath / "poetry.lock").exists())

    def test_install_in_venv(self):
        shutil.rmtree(str(self.venv))
        com = poetry.commands.PoetryInstallInVenvCommand(self.window)

        com.window.show_quick_panel = lambda x, y: True
        com.run()  # do init thing
        com.callback(0)  # run as 0 choice is used

        yield 20000
        # yield self.status

        self.assertTrue(
            (
                self.dirpath
                / ".venv"
                / poetry.compat.VENV_BIN_DIR
                / poetry.compat.PYTHON_EXEC
            ).exists()
        )
        self.assertTrue((self.dirpath / "poetry.lock").exists())
