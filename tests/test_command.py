from unittest import TestCase

from fixtures import poem, PoemTestCase
import sublime


class TestPoem(PoemTestCase):
    def test_poem(self):
        self.assertEqual(poem.PACKAGE_NAME, "poem")

    # def test_open(self):

    def test_python_interpreter(self):
        self.window.run_command("poem_set_python_interpreter")
        project_data = self.window.project_data()
        self.assertEqual(
            project_data,
            {
                "settings": {"python_interpreter": str(self.path / ".venv" /  "bin" / "python")},
                "folders": [{"path": self.dir.name}],
            },
        )
