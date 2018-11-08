from fixtures import PoetryDeferredTestCase


class TestPackageCommands(PoetryDeferredTestCase):
    def test_a_add(self):

        self.window.run_command("poetry_add", args={"custom": "toml"})
        yield self.status
        self.assert_in_toml("toml")

    def test_b_add_dev(self):

        self.window.run_command("poetry_add_dev", args={"custom": "tomlkit"})
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
