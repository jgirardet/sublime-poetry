from unittest import TestCase

from fixtures import poem, PoemTestCase
import sublime

class TestPoem(PoemTestCase):
    def test_poem(self):
        self.assertEqual(poem.PACKAGE_NAME, "Poem")

    def test_open(self):


