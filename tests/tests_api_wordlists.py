import unittest
import json
from dlernen import create_app
from flask import url_for
from mysql.connector import connect
from contextlib import closing


# fetch every value from the database that is supposed to conform to some
# pattern and confirm that it actually does.  we will fetch all of the words,
# and all of the wordlists.  the tests will succeed if the results pass validation.

class ValidateData(unittest.TestCase):
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

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # get all of the wordlists
    def test_get_wordlists(self):
        r = self.client.get(url_for('api_wordlist.get_metadata_multiple'))
        self.assertEqual(r.status_code, 200)
        results = json.loads(r.data)
        self.assertGreater(len(results), 0)

    def test_garbage_payload(self):
        payload = {
            'bull': 'shit'
        }
        url = url_for('api_wordlist.delete_wordlists')
        r = self.client.put(url, json=payload)
        self.assertEqual(400, r.status_code)
