from fixtures import PoetryDeferredTestCase, poetry
from unittest import TestCase, skip
import shutil
import sublime
from unittest.mock import patch, PropertyMock


# @skip("temp")
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

    def test_publish(self):
        if (self.dirpath / "dist").exists():
            shutil.rmtree(str(self.dirpath / "dist"))
        self.window.run_command("poetry_build")
        self.window.run_command("poetry_publish")
        yield self.status
        # self.assertTrue(
        #     (self.dirpath / "dist" / "rien-0.1.0-py2.py3-none-any.whl").exists()
        # )
        # self.assertTrue((self.dirpath / "dist" / "rien-0.1.0.tar.gz").exists())


class TestPublishClass(TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.pp = poetry.commands.PoetryPublishCommand(self.window)
        self.pp.poetry = poetry.poetry.Poetry(self.window)

    def test_get_credential(self):

        # nothing
        with patch.object(poetry.poetry.Poetry, "auth", new_callable=PropertyMock) as auth:
            auth.return_value = {"http-basic": {}}
            self.assertEqual(self.pp.get_credential("foo"), None)

        # tird party
        with patch.object(poetry.poetry.Poetry, "auth", new_callable=PropertyMock) as auth:
            auth.return_value = {"http-basic": {"foo": {"password": "mdp", "username": "login"}}}
            self.assertEqual(self.pp.get_credential("foo"), ("login", "mdp"))

        # tird pypi
        with patch.object(poetry.poetry.Poetry, "auth", new_callable=PropertyMock) as auth:
            auth.return_value = {"http-basic": {"pypi": {"password": "mdp", "username": "login"}}}
            self.assertEqual(self.pp.get_credential("pypi"), ("login", "mdp"))

        # other method
        with patch.object(poetry.poetry.Poetry, "auth", new_callable=PropertyMock) as auth:
            auth.return_value = {"http-basic":{}, 'other_method' : {"pypi": {"password": "mdp", "username": "login"}}}
            self.assertEqual(self.pp.get_credential("pypi"), ("login", "mdp"))
