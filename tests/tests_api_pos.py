import unittest
from dlernen import create_app
from flask import url_for
import json
from pprint import pprint


class APITests(unittest.TestCase):
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

    def test_nothing(self):
        # don't do anything, just make sure setup and teardown work
        pass

    def test_pos_structure(self):
        url = url_for('api_pos.get_pos', _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)

    def test_bullshit_wordid(self):
        url = url_for('api_pos.get_pos_for_word_id', word_id=83674587, _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)

        obj = json.loads(r.data)

        self.assertEqual(0, len(obj))

