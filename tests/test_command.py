from fixtures import poetry, PoetryTestCase
import os
from pathlib import Path


class TestPoetry(PoetryTestCase):
    def test_poetry_package_name(self):
        self.assertEqual(poetry.PACKAGE_NAME, "poetry")

    def test_set_python_interpreter(self):
        self.create_venv()
        self.window.run_command("poetry_set_python_interpreter")
        project_data = self.window.project_data()

        if (
            "TRAVIS" in os.environ and os.environ["TRAVIS_OS_NAME"] == "linux"
        ):  # because poetry ignore .venv ifVIRTUAL_ENV set
            base = Path(os.environ["VIRTUAL_ENV"]).resolve()
        else:
            base = self.venv.resolve()
        self.assertEqual(
            project_data,
            {
                "settings": {"python_interpreter": str(base / "bin" / "python")},
                "folders": [{"path": self.dir.name}],
            },
        )
