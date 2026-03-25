import unittest
from flask import url_for
from dlernen import create_app, common
from dlernen.dlernen_json_schema import get_validator, \
    DISPLAYABLE_WORD_ARRAY_SCHEMA
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

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
        )

        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings'))
        cls.keyword_mappings = json.loads(r.data)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def createWord(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))

        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        word_id = obj['word_id']

        return word, word_id

    # make sure setup works
    def test_nothing(self):
        pass

    def test_get_displayable_words(self):
        word1, word1_id = self.createWord()
        self.addCleanup(cleanupWordID, self.client, word1_id)

        word2, word2_id = self.createWord()
        self.addCleanup(cleanupWordID, self.client, word2_id)

        with closing(connect(**self.app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            result = common.get_displayable_words([word1_id, word2_id], cursor)
            get_validator(DISPLAYABLE_WORD_ARRAY_SCHEMA).validate(result)
