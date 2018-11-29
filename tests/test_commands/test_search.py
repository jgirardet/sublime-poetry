import sublime
from fixtures import PoetryDeferredTestCase, poetry
from unittest.mock import patch, MagicMock


class TestSearch(PoetryDeferredTestCase):
    def setUp(self):
        super().setUp()
        self.ps = poetry.commands.PoetrySearchCommand(self.window)

    def new_view(self):
        return self.window.active_view().name() == "poetry_search_result"

    def test_search(self):

        # with patch("sublime_plugin.WindowCommand.show_input_panel"):
        # self.window.run_command('poetry_search')
        self.ps.window.show_input_panel = MagicMock(
            return_value=self.ps.search("black")
        )
        self.ps.run()
        yield self.new_view
        view = self.window.active_view()
        content = view.substr(sublime.Region(0, view.size()))

        # check two lines per result
        self.assertTrue("black" in content)
        self.assertTrue("black" in content)

        # only search in name

        self.assertTrue("spops" not in content)
