from unittest import TestCase

from fixtures import poem


class TestPoem(TestCase):
    def test_poem(self):
        self.assertEqual(poem.PACKAGE_NAME, "Poem")