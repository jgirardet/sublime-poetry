from fixtures import poetry, PoetryDeferredTestCase
import os
from pathlib import Path
from unittest.mock import patch, PropertyMock, MagicMock


class TestConfig(PoetryDeferredTestCase):
    def setUp(self):
        super().setUp()
        self.pc = poetry.commands.PoetryConfigCommand(self.window)
        self.pc.run_poetry_command = MagicMock()

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

    @patch.object(
        poetry.poetry.Poetry,
        "config",
        new_callable=PropertyMock,
        return_value={"settings": {"foo": "bar"}, "repositories": {}},
    )
    @patch.object(poetry.poetry.sublime, "yes_no_cancel_dialog", return_value=1)
    def test_unset_text(self, config, yes_no):
        self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(0)
        self.pc.run()
        self.pc.run_poetry_command.assert_called_with("config settings.foo --unset")

    @patch.object(
        poetry.poetry.Poetry,
        "config",
        new_callable=PropertyMock,
        return_value={"settings": {"foo": "bar"}, "repositories": {}},
    )
    @patch.object(poetry.poetry.sublime, "yes_no_cancel_dialog", return_value=2)
    def test_modif_text(self, config, yes_no):
        self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(0)
        # self.pc.window.show_input_panel = lambda v, w, x, y, z:  self.pc.run_poetry_command(y, "new_bar")
        self.pc.run_input_command = lambda x, y, w: self.pc.run_poetry_command(
            y, "new_bar"
        )
        self.pc.run()
        self.pc.run_poetry_command.assert_called_with("config settings.foo", "new_bar")

    @patch.object(
        poetry.poetry.Poetry,
        "config",
        new_callable=PropertyMock,
        return_value={"settings": {"foo": True}, "repositories": {}},
    )
    def test_toggle_true(self, config):
        self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(0)
        # self.pc.window.show_input_panel = lambda v, w, x, y, z:  self.pc.run_input_command.to_run('new_bar')
        # self.pc.run_input_command = lambda x, y, w: self.pc.run_poetry_command(y, "new_bar")
        self.pc.run()
        self.pc.run_poetry_command.assert_called_with("config settings.foo false")

    @patch.object(
        poetry.poetry.Poetry,
        "config",
        new_callable=PropertyMock,
        return_value={"settings": {"foo": False}, "repositories": {}},
    )
    def test_toggle_false(self, config):
        self.pc.window.show_quick_panel = lambda v, w, x, y: self.pc.dispatch(0)
        # self.pc.window.show_input_panel = lambda v, w, x, y, z:  self.pc.run_input_command.to_run('new_bar')
        # self.pc.run_input_command = lambda x, y, w: self.pc.run_poetry_command(y, "new_bar")
        self.pc.run()
        self.pc.run_poetry_command.assert_called_with("config settings.foo true")
