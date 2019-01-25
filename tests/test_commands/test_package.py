from fixtures import PoetryDeferredTestCase, poetry
from unittest.mock import patch


class TestPackageCommands(PoetryDeferredTestCase):
    """ test add/remove commands """

    def test_a_add(self):

        self.window.run_command("poetry_add", args={"custom": "toml"})
        yield self.status
        self.assert_in_toml("toml")

    def test_b_add_dev(self):

        self.window.run_command("poetry_add", args={"custom": "tomlkit", "dev": True})
        yield self.status
        self.assert_in_toml("tomlkit", "dev")

    def test_c_remove(self):

        self.window.run_command("poetry_remove", args={"custom": "toml"})
        yield self.status
        self.assert_not_in_toml("toml")

    def test_d_remove_dev(self):

        self.window.run_command("poetry_remove", args={"custom": "-D tomlkit"})
        yield self.status
        self.assert_not_in_toml("tomlkit", "dev")


class TestUnderCursor(PoetryDeferredTestCase):
    def test_add_under_cursor_dev(self):
        self.view.set_name("poetry_search_result")

        self.view.run_command("insert", args={"characters": "toml (1.1.1)"})
        with patch("sublime.yes_no_cancel_dialog", return_value=1):
            self.view.run_command("poetry_add_package_under_cursor")

        yield self.status

        self.assert_in_toml("toml", "dev")
        self.assert_not_in_toml("toml")

    def test_add_under_cursor_regular(self):
        self.view.set_name("poetry_search_result")

        self.view.run_command("insert", args={"characters": "toml (1.1.1)"})
        with patch("sublime.yes_no_cancel_dialog", return_value=2):
            self.view.run_command("poetry_add_package_under_cursor")

        yield self.status

        self.assert_in_toml("toml")


class TestVersionCommands(PoetryDeferredTestCase):
    """test version command"""

    def setUp(self):
        super().setUp()
        self.pv = poetry.commands.PoetryVersionCommand(self.window)

    def test_a_patch(self):
        self.pv.run("patch")
        yield self.status
        self.assertEqual("0.1.1", self.pv.poetry.package_version)

    def test_b_minor(self):
        self.pv.run("minor")
        yield self.status
        self.assertEqual("0.2.0", self.pv.poetry.package_version)

    def test_d_current_choices(self):
        self.pv.window.show_quick_panel = lambda x, y, z: self.pv._run_version(-0)
        a = self.pv.input("args")
        # yield 1000
        self.assertEqual(
            a.list_items(),
            [
                "****** current 0.2.0 ******",
                "patch",
                "minor",
                "major",
                "prepatch",
                "preminor",
                "premajor",
                "prerelease",
            ],
        )
