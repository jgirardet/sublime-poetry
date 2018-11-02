from fixtures import poetry, PoetryTestCase, BLANK


class TestPoetry(PoetryTestCase):
    def test_poetry(self):
        self.assertEqual(poetry.PACKAGE_NAME, "poetry")

    def test_test_case(self):
        self.assertEqual(self.pyproject.read_text(), BLANK)
        self.assertEqual(
            str(self.dirpath), self.window.project_data()["folders"][0]["path"]
        )
