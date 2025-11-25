import unittest
import jsonschema
from dlernen import dlernen_json_schema, create_app
from flask import url_for
import json
from pprint import pprint


# FIXME - correcting the spelling of a word through the UI isn't working
#   special case of correcting the spelling of an unknown word before it is added

# TODO:  make sure proper cleanup happens if any assertions fail on status code values.  setup/teardown?


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

    def test_real_quiz_data(self):
        with self.app.test_request_context():
            url = url_for('api_quiz.quiz_data', quiz_key='plurals', _external=True)
            r = self.client.get(url)
            self.assertEqual(200, r.status_code)
            quiz_data = json.loads(r.data)

            jsonschema.validate(quiz_data, dlernen_json_schema.QUIZ_DATA_RESPONSE_SCHEMA)

    def test_empty_quiz_data_no_match(self):
        with self.app.test_request_context():
            url = url_for('api_quiz.get_quiz_by_key', quiz_key='aoeuaoeuaoeu', _external=True)
            r = self.client.get(url)
            self.assertEqual(404, r.status_code)

    def test_get_word_by_word_exact(self):
        with self.app.test_request_context():
            url = url_for('api_word.get_word', word='verderben', _external=True)
            r = self.client.get(url)
            self.assertEqual(200, r.status_code)
            results = json.loads(r.data)
            self.assertGreater(len(results), 0)
            jsonschema.validate(results, dlernen_json_schema.WORDS_RESPONSE_SCHEMA)

    def test_get_word_no_match(self):
        with self.app.test_request_context():
            url = url_for('api_word.get_word', word='anehuintaoedhunateohdu', _external=True)
            r = self.client.get(url)
            self.assertEqual(404, r.status_code)

    def test_get_word_by_word_partial(self):
        with self.app.test_request_context():
            url = url_for('api_word.get_word', word='geh', partial=True, _external=True)
            r = self.client.get(url)
            self.assertEqual(200, r.status_code)
            results = json.loads(r.data)
            self.assertGreater(len(results), 0)
            jsonschema.validate(results, dlernen_json_schema.WORDS_RESPONSE_SCHEMA)

    def test_get_words_empty_list_1(self):
        with self.app.test_request_context():
            url = url_for('api_word.get_words', _external=True)
            payload = {
            }

            r = self.client.put(url, json=payload)
            self.assertEqual(200, r.status_code)
            result = json.loads(r.data)
            self.assertEqual([], result)

    def test_get_words_empty_list_2(self):
        with self.app.test_request_context():
            url = url_for('api_word.get_words', _external=True)
            payload = {
                "word_ids": []
            }

            r = self.client.put(url, json=payload)
            self.assertEqual(200, r.status_code)
            result = json.loads(r.data)
            self.assertEqual([], result)
