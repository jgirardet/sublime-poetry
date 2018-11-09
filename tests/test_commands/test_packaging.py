from fixtures import PoetryDeferredTestCase
import shutil


class TestPackagingCommands(PoetryDeferredTestCase):
    def setUp(self):
        super().setUp()
        if (self.dirpath / "poetry.lock").exists():
            (self.dirpath / "poetry.lock").unlink()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # cls.window.run_command("poetry_install")
        # yield 4000
        rien = cls.dirpath / "rien"
        rien.mkdir()
        (rien / "__init__.py").touch()

    def test_build(self):
        if (self.dirpath / "dist").exists():
            shutil.rmtree(str(self.dirpath / "dist"))
        self.window.run_command("poetry_build")
        yield self.status
        self.assertTrue(
            (self.dirpath / "dist" / "rien-0.1.0-py2.py3-none-any.whl").exists()
        )
        self.assertTrue((self.dirpath / "dist" / "rien-0.1.0.tar.gz").exists())
