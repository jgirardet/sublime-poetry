from fixtures import poetry, PoetryDeferredTestCase
import os
from pathlib import Path
import sublime


class TestInterpreter(PoetryDeferredTestCase):
    def test_aa_set_python_interpreter(self):
        self.window.run_command("poetry_set_python_interpreter")
        yield 2000
  
        project_data = self.window.project_data()


        if (
            "TRAVIS" in os.environ and os.environ["TRAVIS_OS_NAME"] == "linux"
        ):  # because poetry ignore .venv ifVIRTUAL_ENV set
            base = Path(os.environ["VIRTUAL_ENV"]).resolve()
        else:
            base = self.venv.resolve()

        if sublime.platform() == "windows":
            base = Path(str(base).lower())

        self.assertEqual(
            project_data,
            {
                "settings": {
                    "python_interpreter": str(
                        base / poetry.compat.VENV_BIN_DIR / "python"
                    )
                },
                "folders": [{"path": self.dir.name}],
            },
        )
