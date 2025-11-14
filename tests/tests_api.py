import unittest
import jsonschema
import requests
from dlernen import dlernen_json_schema, config, create_app
from flask import url_for
import json
from pprint import pprint
import random
import string


# FIXME - correcting the spelling of a word through the UI isn't working
#   special case of correcting the spelling of an unknown word before it is added

# TODO:  make sure proper cleanup happens if any assertions fail on status code values.  setup/teardown?


class APITests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            SERVER_NAME='localhost.localdomain:5000'
        )

        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_dummy(self):
        with self.app.test_request_context():
            pprint(self.app.config)
            url = url_for('api_misc.get_pos', _external=True)
            print(url)

    def test_pos_structure(self):
        with self.app.test_request_context():
            url = url_for('api_misc.get_pos', _external=True)
            r = self.client.get(url)
            pos_structure = json.loads(r.data)

            jsonschema.validate(pos_structure, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

    def test_real_quiz_data(self):
        url = "%s/api/quiz_data/%s" % (config.Config.DB_URL, 'plurals')
        r = requests.get(url)
        quiz_data = r.json()

        jsonschema.validate(quiz_data, dlernen_json_schema.QUIZ_DATA_RESPONSE_SCHEMA)

    def test_empty_quiz_data_no_match(self):
        url = "%s/api/quiz_data/%s" % (config.Config.DB_URL, 'aoeuaoeuaeou')
        r = requests.get(url)
        self.assertEqual(404, r.status_code)

    def test_get_word_by_word_exact(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/verderben")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDS_RESPONSE_SCHEMA)

    def test_get_word_no_match(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/anehuintaoedhunateohdu")
        self.assertEqual(404, r.status_code)

    def test_get_word_by_word_partial(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/geh?partial=true")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDS_RESPONSE_SCHEMA)

    def test_get_words_empty_list_1(self):
        url = "%s/api/words" % config.Config.DB_URL
        payload = {
        }

        r = requests.put(url, json=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_get_words_empty_list_2(self):
        url = "%s/api/words" % config.Config.DB_URL
        payload = {
            "word_ids": []
        }

        r = requests.put(url, json=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)


class APIWordlists(unittest.TestCase):
    # get all wordlists
    def test_real_wordlist(self):
        r = requests.get(config.Config.BASE_URL + "/api/wordlists")
        self.assertEqual(r.status_code, 200)
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDLISTS_RESPONSE_SCHEMA)


