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

    def test_get_wordlists(self):
        r = self.client.get(url_for('api_wordlists.get_wordlists', _external=True))
        self.assertEqual(r.status_code, 200)
        results = json.loads(r.data)
        self.assertGreater(len(results), 0)

    def test_get_words(self):
        limit = 1000
        offset = 0

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
                r = self.client.put(url_for('api_words.get_words_from_word_ids', _external=True), json=payload)
                self.assertEqual(r.status_code, 200)

                offset += limit
                cursor.execute(sql, {'offset': offset, 'limit': limit})
                rows = cursor.fetchall()

