from fixtures import poetry, PoetryDeferredTestCase
import os

# from pathlib import Path
from unittest.mock import patch, PropertyMock, MagicMock
import tempfile

Poetry = poetry.poetry.Poetry
Path = poetry.utils.Path
import toml


class TestConfig(PoetryDeferredTestCase):
    def setUp(self):
        super().setUp()
        self.pc = poetry.commands.PoetryConfigCommand(self.window)

        # backup config file
        temp_bak = tempfile.NamedTemporaryFile(delete=False)
        temp_bak.close()
        temp_bak_auth = tempfile.NamedTemporaryFile(delete=False)
        temp_bak_auth.close()
        self.config_bak = poetry.utils.Path(temp_bak.name)
        self.auth_bak = poetry.utils.Path(temp_bak_auth.name)
        self.po = poetry.poetry.Poetry(self.window)
        self.config_file = Path(self.po.appdirs()["config"], "config.toml")
        self.auth_file = Path(self.po.appdirs()["config"], "auth.toml")
        self.config_bak.write_text(self.config_file.read_text())
        self.auth_bak.write_text(self.auth_file.read_text())

    def tearDown(self):
        # restore config files
        self.config_file.write_text(self.config_bak.read_text())
        self.config_bak.unlink()
        self.auth_file.write_text(self.auth_bak.read_text())
        self.auth_bak.unlink()

    def choose(self, key):
        """Select good key for tests"""
        for i, c in enumerate(self.pc.fconfig_str):
            if key in c[0]:
                return i

    def test_unset_text(self):
        with patch.object(
            poetry.commands.sublime, "yes_no_cancel_dialog", return_value=1
        ) as yes_no:
            file = toml.loads(self.config_file.read_text())
            file = {"settings": {"virtualenvs": {"path": "nothing"}}}
            self.config_file.write_text(toml.dumps(file))

            self.assertEqual(
                self.po.config["settings"]["virtualenvs"]["path"], "nothing"
            )

            self.pc.run(("settings.virtualenvs.path", "nothing"))
            yield self.status
            self.assertEqual(
                self.po.config["settings"]["virtualenvs"]["path"],
                str(Path(self.po.appdirs()["cache"], "virtualenvs")),
            )

    def test_modif_text(self):
        with patch.object(
            poetry.commands.sublime, "yes_no_cancel_dialog", return_value=2
        ) as yes_no:
            file = toml.loads(self.config_file.read_text())
            file = {"settings": {"virtualenvs": {"path": "nothing"}}}
            self.config_file.write_text(toml.dumps(file))
            self.assertEqual(
                self.po.config["settings"]["virtualenvs"]["path"], "nothing"
            )

            self.pc.run_input_command = lambda x, y, w: self.pc.run_poetry_command(
                y, "new_bar"
            )
            self.pc.run(["settings.virtualenvs.path", "nothing"])
            yield self.status
            self.assertEqual(
                self.po.config["settings"]["virtualenvs"]["path"], "new_bar"
            )

    def test_modif_cred(self):
        with patch.object(
            poetry.commands.sublime, "yes_no_cancel_dialog", return_value=2
        ) as yes_no:
            self.config_file.write_text(
                toml.dumps({"repositories": {"nothing": {"url": "labas"}}})
            )
            self.auth_file.write_text(
                toml.dumps(
                    {"http-basic": {"one": {"username": "u_one", "password": "u_pwd"}}}
                )
            )

            self.assertEqual(
                self.po.auth["http-basic"]["one"],
                {"username": "u_one", "password": "u_pwd"},
            )

            self.pc.run_input_command = lambda x, y, w: self.pc.run_poetry_command(
                y, "new bar"
            )
            #         )
            self.pc.run(["http-basic.one", "u_one u_password"])
            yield self.status
            self.assertEqual(
                self.po.auth["http-basic"]["one"],
                {"username": "new", "password": "bar"},
            )

    def test_unset_cred(self):
        with patch.object(
            poetry.commands.sublime, "yes_no_cancel_dialog", return_value=1
        ) as yes_no:
            self.config_file.write_text(
                toml.dumps({"repositories": {"nothing": {"url": "labas"}}})
            )
            self.auth_file.write_text(
                toml.dumps(
                    {"http-basic": {"one": {"username": "u_one", "password": "u_pwd"}}}
                )
            )

            self.assertEqual(
                self.po.auth["http-basic"]["one"],
                {"username": "u_one", "password": "u_pwd"},
            )

            self.pc.run(["http-basic.one", "u_one u_password"])
            yield self.status
            self.assertTrue("one" not in self.po.auth["http-basic"])

    def test_toggle_true_false(self):
        file = toml.loads(self.config_file.read_text())
        file = {"settings": {"virtualenvs": {"create": True}}}
        self.config_file.write_text(toml.dumps(file))

        self.assertEqual(self.po.config["settings"]["virtualenvs"]["create"], True)

        # true to False
        result = False
        self.pc.run(["settings.virtualenvs.create", True])
        yield self.status
        self.assertEqual(self.po.config["settings"]["virtualenvs"]["create"], result)

        # false to true
        self.pc.run(["settings.virtualenvs.create", result])
        yield self.status
        self.assertEqual(self.po.config["settings"]["virtualenvs"]["create"], True)

    def test_add_repo(self):
        self.pc.run_input_command = lambda x, y, w: self.pc.run_poetry_command(
            y, "repos.newone http://newone"
        )
        self.pc.run(("repo", "+"))
        yield self.status
        self.assertEqual(
            self.po.config["repositories"]["newone"]["url"], "http://newone"
        )
