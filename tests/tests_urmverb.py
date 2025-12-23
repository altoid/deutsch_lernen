import unittest
from dlernen import app_urmverb, create_app
import random
import string


class TestURMVerb(unittest.TestCase):
    app = None
    app_context = None
    client = None

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
        )

        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    irregular_verbs = [
        'sehen',
        'haben'
    ]

    regular_verbs = [
        'abstellen',
    ]

    not_verbs = [
        'jedenfalls',
    ]

    misfits = [
        ''.join(random.choices(string.ascii_lowercase, k=10)),  # not in the dictionary, hopefully
        'verbnosps',  # fake word created for this test.
        'verbnotps',  # ditto
    ]

    def test_irregular_verbs(self):
        with self.app.test_request_context():
            for verb in self.irregular_verbs:
                with self.subTest(verb=verb):
                    self.assertTrue(app_urmverb.is_irregular_verb(verb))

    def test_regular_verbs(self):
        with self.app.test_request_context():
            for verb in self.regular_verbs:
                with self.subTest(verb=verb):
                    self.assertFalse(app_urmverb.is_irregular_verb(verb))

    def test_not_verbs(self):
        with self.app.test_request_context():
            for verb in self.not_verbs:
                with self.subTest(verb=verb):
                    self.assertIsNone(app_urmverb.is_irregular_verb(verb))

    def test_misfits(self):
        with self.app.test_request_context():
            for verb in self.not_verbs:
                with self.subTest(verb=verb):
                    self.assertIsNone(app_urmverb.is_irregular_verb(verb))

