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
            # select the good one

            self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(
                self.choose("path")
            )
            self.pc.run()
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

            self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(
                self.choose("path")
            )
            self.pc.run_input_command = lambda x, y, w: self.pc.run_poetry_command(
                y, "new_bar"
            )
            self.pc.run()
            yield self.status
            self.assertEqual(
                self.po.config["settings"]["virtualenvs"]["path"], "new_bar"
            )

    def test_toggle_true(self):
        file = toml.loads(self.config_file.read_text())
        file = {"settings": {"virtualenvs": {"create": True}}}
        self.config_file.write_text(toml.dumps(file))
        self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(
            self.choose("create")
        )
        self.assertEqual(self.po.config["settings"]["virtualenvs"]["create"], True)
        self.pc.run()
        yield self.status
        self.assertEqual(self.po.config["settings"]["virtualenvs"]["create"], False)

    def test_toggle_false(self):
        file = toml.loads(self.config_file.read_text())
        file = {"settings": {"virtualenvs": {"create": False}}}
        self.config_file.write_text(toml.dumps(file))

        self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(
            self.choose("create")
        )
        self.assertEqual(self.po.config["settings"]["virtualenvs"]["create"], False)
        self.pc.run()
        yield self.status
        self.assertEqual(self.po.config["settings"]["virtualenvs"]["create"], True)

    def test_add_repo(self):
        self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(
            self.choose("Add a new repo")
        )
        self.pc.run_input_command = lambda x, y, w: self.pc.run_poetry_command(
            y, "repos.newone http://newone"
        )
        self.pc.run()
        yield self.status
        self.assertEqual(
            self.po.config["repositories"]["newone"]["url"], "http://newone"
        )

    def test_configure_credential_call(self):
        def init():
            self.config_file.write_text(
                toml.dumps({"repositories": {"nothing": {"url": "labas"}}})
            )
            self.auth_file.write_text(
                toml.dumps(
                    {"http-basic": {"one": {"username": "u_one", "password": "u_pwd"}}}
                )
            )

        def run_test(choice):
            init()
            self.pc.run_after_command = MagicMock()
            with patch.object(self.pc.window, "show_quick_panel") as sq:
                self.pc.run()
                with patch.object(
                    self.pc.window,
                    "show_input_panel",
                    lambda a, z, e, r, t: self.pc._run_credentials_command(
                        "name pwd", choice
                    ),
                ) as si:
                    self.pc._callback_credentials(choice)

        # pypi added if was unset
        run_test(0)
        yield self.status
        self.assertEqual(
            Poetry(self.window).auth["http-basic"]["pypi"],
            {"username": "name", "password": "pwd"},
        )

        # existing repo in auth.toml
        run_test(2)
        yield self.status
        self.assertEqual(
            Poetry(self.window).auth["http-basic"]["one"],
            {"username": "name", "password": "pwd"},
        )

        # existing repo in config.toml
        run_test(1)
        yield self.status
        self.assertEqual(
            Poetry(self.window).auth["http-basic"]["nothing"],
            {"username": "name", "password": "pwd"},
        )
