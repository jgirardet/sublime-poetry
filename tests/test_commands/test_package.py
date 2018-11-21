from fixtures import PoetryDeferredTestCase, poetry


class TestPackageCommands(PoetryDeferredTestCase):
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


class TestVersionCommands(PoetryDeferredTestCase):
    def setUp(self):
        super().setUp()
        self.pv = poetry.commands.PoetryVersionCommand(self.window)

    def test_a_patch(self):
        self.pv.window.show_quick_panel = lambda x, y, z: self.pv._run_version(1)
        self.pv.run()
        yield self.status
        self.assertEqual("0.1.1", self.pv.poetry.package_version)

    def test_b_minor(self):
        self.pv.window.show_quick_panel = lambda x, y, z: self.pv._run_version(2)
        self.pv.run()
        yield self.status
        self.assertEqual("0.2.0", self.pv.poetry.package_version)

    def test_c_cancel(self):
        self.pv.window.show_quick_panel = lambda x, y, z: self.pv._run_version(-1)
        self.pv.run()
        yield 1000
        self.assertEqual("0.2.0", self.pv.poetry.package_version)

    def test_d_current(self):
        self.pv.window.show_quick_panel = lambda x, y, z: self.pv._run_version(-0)
        self.pv.run()
        yield 1000
        self.assertEqual("0.2.0", self.pv.poetry.package_version)
