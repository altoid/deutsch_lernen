import unittest
import json
from dlernen import create_app
from flask import url_for
from pprint import pprint
import random
import string
from mysql.connector import connect
from contextlib import closing


# fetch every value from the database that is supposed to conform to some
# pattern and confirm that it actually does.  we will fetch all of the words,
# and all of the wordlists.  the tests will succeed if the results pass validation.

class ValidateData(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            SERVER_NAME='localhost.localdomain:5000'
        )

        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        with self.app.test_request_context():
            pass

    def tearDown(self):
        self.app_context.pop()

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    def test_get_wordlists(self):
        with self.app.test_request_context():
            r = self.client.get(url_for('api_wordlist.get_wordlists', _external=True))
            self.assertEqual(r.status_code, 200)
            results = json.loads(r.data)
            self.assertGreater(len(results), 0)

    def test_get_words(self):
        limit = 1000
        offset = 0
        with self.app.test_request_context():
            with closing(connect(**self.app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
                # fetch all the word ids 1000 at a time
                sql = """
                select id
                from word
                limit %(offset)s, %(limit)s
                """

                cursor.execute(sql, {'offset': offset, 'limit': limit})
                rows = cursor.fetchall()

                while len(rows) > 0:
                    payload = {
                        'word_id': list(map(lambda x: x['id'], rows))
                    }
                    r = self.client.put(url_for('api_word.get_words', _external=True), json=payload)
                    self.assertEqual(r.status_code, 200)

                    offset += limit
                    cursor.execute(sql, {'offset': offset, 'limit': limit})
                    rows = cursor.fetchall()

