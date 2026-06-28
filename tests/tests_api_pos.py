import unittest
from dlernen import create_app
from flask import url_for
import json
import random
import string
from dlernen.json_schema_patterns import DEFINITION, ATTRIBUTES
from pprint import pprint


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id))


class APITests(unittest.TestCase):
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

        r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings'))
        cls.keyword_mappings = json.loads(r.data)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def test_nothing(self):
        # don't do anything, just make sure setup and teardown work
        pass

    def test_pos_structure(self):
        url = url_for('api_pos.get_pos')
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)

    def test_bullshit_wordid(self):
        url = url_for('api_pos.get_pos_for_word_id', word_id=83674587)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)

        obj = json.loads(r.data)

        self.assertEqual(0, len(obj))

    def test_get_pos_by_word(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        def_noun = "noun %s" % ''.join(random.choices(string.ascii_lowercase, k=10))

        payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids'][self.POSName.NOUN],
            ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['plural'],
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids'][DEFINITION],
                    "attrvalue": def_noun
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.addCleanup(cleanupWordID, self.client, obj['word_id'])
        word_id_1 = obj['word_id']

        def_adj = "adjective %s" % ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids'][self.POSName.ADJECTIVE],
            ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids'][DEFINITION],
                    "attrvalue": def_adj
                }
            ]
        }

        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(201, r.status_code)

        obj = json.loads(r.data)
        self.addCleanup(cleanupWordID, self.client, obj['word_id'])
        word_id_2 = obj['word_id']

        url = url_for('api_pos.get_pos_for_word', word=word)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)

        obj = json.loads(r.data)

        # right now, if the object passes validation, that's good enough.


class APIPosName(unittest.TestCase):
    # make sure dynamically-created POSName Enum class is well-behaved

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

    def test1(self):
        self.assertEqual('Noun', self.POSName.NOUN)

    def test2(self):
        self.assertTrue(self.POSName.SEPARABLE_PREFIX in self.POSName)

    def test3(self):
        self.assertTrue('Separable Prefix' in self.POSName)


