from fixtures import poetry, PoetryTestCase, PoetryDeferredTestCase
import os
from pathlib import Path
import sublime
import time


class TestPoetry(PoetryDeferredTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_set_python_interpreter(self):
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

    def status(self):

        if "succes" in self.view.get_status("poetry"):
            return True

        if "fail" in self.view.get_status("poetry"):
            return True

    def test_install(self):

        self.window.run_command("poetry_install")
        yield self.status
        # yield 2000
        self.assertTrue((self.dirpath / "poetry.lock").exists())
        (self.dirpath / "poetry.lock").unlink()

    def test_install_no_dev(self):
        self.window.run_command("poetry_install_no_dev")

        yield self.status
        

        self.assertTrue((self.dirpath / "poetry.lock").exists())
        (self.dirpath / "poetry.lock").unlink()

