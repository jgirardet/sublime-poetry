from fixtures import poetry, PoetryDeferredTestCase
import os

# from pathlib import Path
from unittest.mock import patch, PropertyMock, MagicMock
import tempfile

Path = poetry.utils.Path
import toml


class TestConfig(PoetryDeferredTestCase):
    def setUp(self):
        super().setUp()
        self.pc = poetry.commands.PoetryConfigCommand(self.window)

        # backup config file
        temp_bak = tempfile.NamedTemporaryFile(delete=False)
        temp_bak.close()
        self.config_bak = poetry.utils.Path(temp_bak.name)
        self.po = poetry.poetry.Poetry(self.window)
        self.config_file = Path(self.po.appdirs()["config"], "config.toml")
        self.config_bak.write_text(self.config_file.read_text())

    def tearDown(self):
        # restore config files
        self.config_file.write_text(self.config_bak.read_text())
        self.config_bak.unlink()

    # def test_auth_repo_pypy_selected(self):
    # with patch.object(
    #     poetry.poetry.Poetry, "config", new_callable=PropertyMock
    # ) as config:
    #     config.
    #     self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(0)
    #     with patch.object(
    #         poetry.poetry.Poetry, "auth", new_callable=PropertyMock
    #     ) as auth:
    #         auth.return_value = {
    #             "http-basic": {"pypi": {"password": "mdp", "username": "login"}}
    #         }
    #         # self.pp.window.show_inpout_panel = MagicMock(return_value="login, mdp")
    #         # self.pp.get_credential =  lambda x: ('login', 'mdp')
    #         self.pp.run()
    #         self.pp.run_poetry_command.assert_called_with(
    #             "publish --username=login --password=mdp"
    #         )

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
                "/home/jimmy/.cache/pypoetry/virtualenvs",
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
