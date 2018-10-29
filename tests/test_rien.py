from unittest import TestCase

from fixtures import poem, PoemTestCase, BLANK
import sublime

class TestPoem(PoemTestCase):
    def test_poem(self):
        self.assertEqual(poem.PACKAGE_NAME, "Poem")

    # def test_open(self):

    def test_test_case(self):
        self.assertEqual(self.toml.read_text(), BLANK)
        self.assertEqual(str(self.dirpath), self.window.project_data()['folders'][0]['path'])

