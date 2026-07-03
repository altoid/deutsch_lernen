import unittest
from flask import url_for
from dlernen import create_app, common
import json
import random
import string
from mysql.connector import connect
from contextlib import closing
from pprint import pprint


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id))


class TestCommon(unittest.TestCase):
    app = None
    app_context = None
    client = None
    POSName = None

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
        )

        cls.POSName = cls.app.extensions.get('POSName')
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def createWord(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))

        add_payload = {
            "word": word,
            "pos_name": self.POSName.ADJECTIVE,
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        return word, word_id

    # make sure setup works
    def test_nothing(self):
        pass

    # test that validation happens on get_displayable_words.
    def test_get_displayable_words(self):
        word1, word1_id = self.createWord()
        word2, word2_id = self.createWord()

        with closing(connect(**self.app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            result = common.get_displayable_words(cursor, [word1_id, word2_id])

