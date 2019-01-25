from fixtures import PoetryDeferredTestCase

# @skip("mokm")
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
