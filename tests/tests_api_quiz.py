import unittest
import random
import string
from dlernen import dlernen_json_schema as js, create_app
from flask import url_for
import json
from pprint import pprint


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id, _external=True))


def cleanupWordlistID(client, wordlist_id):
    client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id, _external=True))


class APIQuizGetWordToTest(unittest.TestCase):
    # unit tests for api_quiz.get_word_to_test.  this api call will return an array of QUIZ_RESPONSE_SCHEMA
    # objects of length at most 1 when using parameters that are legit.

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

    def setUp(self):
        # create a wordlist with a fake verb
        pass

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    # see if we fetch the word in the wordlist when using the api correctly
    def test_basic(self):
        raise NotImplementedError

    # use a valid quiz key but one that won't return anything:  genders for a verb
    def test_nonmatching_quiz_key(self):
        raise NotImplementedError

    def test_undefined_quiz_key(self):
        raise NotImplementedError

    # should return something from the complete dictionary
    def test_no_wordlist(self):
        raise NotImplementedError

    def test_undefined_query(self):
        raise NotImplementedError

    def test_empty_wordlist(self):
        raise NotImplementedError

    def test_undefined_wordlist(self):
        raise NotImplementedError


class APIQuizGetWordToTestSingleWordlist(unittest.TestCase):
    # unit tests for api_quiz.get_word_to_test_single_wordlist, which lets us search by tags.  this api call will
    # return an array of QUIZ_RESPONSE_SCHEMA
    # objects of length at most 1 when using parameters that are legit.

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

    def setUp(self):
        # create a wordlist with a two fake verbs, and tag one of them.
        pass

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    # see if we fetch the word in the wordlist when using the api correctly
    def test_basic_with_tag(self):
        raise NotImplementedError

    # see if we fetch both words in the wordlist when using the api correctly
    def test_basic_without_tag(self):
        raise NotImplementedError

    # use a valid quiz key but one that won't return anything:  genders for a verb
    def test_nonmatching_quiz_key(self):
        raise NotImplementedError

    def test_undefined_quiz_key(self):
        raise NotImplementedError

    def test_undefined_query(self):
        raise NotImplementedError

    def test_undefined_wordlist(self):
        raise NotImplementedError

    def test_empty_wordlist(self):
        raise NotImplementedError


class APIQuizTestGetAllAttrValuesForQuiz(unittest.TestCase):
    # unit tests for api_quiz.get_all_attr_values_for_quiz, which gives us, for a single word,
    # all the attr values that are defined by a quiz.  even if those attribute values are not set.  this api
    # call will return an array of QUIZ_RESPONSE_SCHEMA objects.  we will use the 'present_indicative'.
    #
    # objects of length at most 1 when using parameters that are legit.

    app = None
    app_context = None
    client = None
    QUIZ_KEY = 'present_indicative'

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
        )

        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings', _external=True))
        cls.keyword_mappings = json.loads(r.data)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def setUp(self):
        # create a wordlist with a fake verb, but don't set all of the attributes
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist_id)

        self.word = ''.join(random.choices(string.ascii_lowercase, k=11))
        attrkeys = [
            # some are comment out because we aren't providing values for all of them
            'first_person_singular',
            'second_person_singular',
            # 'third_person_singular',
            # 'first_person_plural',
            'second_person_plural',
            'third_person_plural',
        ]
        attributes = [
            {
                "attribute_id": self.keyword_mappings['attribute_names_to_ids'][k],
                "attrvalue": k,
            }
            for k in attrkeys
        ]
        add_payload = {
            "word": self.word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['verb'],
            js.ATTRIBUTES: attributes
        }

        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.word_id = obj['word_id']

        self.addCleanup(cleanupWordID, self.client, self.word_id)

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    # see if we fetch the word in the wordlist when using the api correctly
    def test_basic(self):
        url = url_for('api_quiz.get_all_attr_values_for_quiz',
                      quiz_key=self.QUIZ_KEY, word_id=self.word_id, _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        expected = [{'attribute_id': 6,
                     'attrkey': 'first_person_singular',
                     'attrvalue': 'first_person_singular',
                     'quiz_id': 4,
                     'word': self.word,
                     'word_id': self.word_id},
                    {'attribute_id': 7,
                     'attrkey': 'second_person_singular',
                     'attrvalue': 'second_person_singular',
                     'quiz_id': 4,
                     'word': self.word,
                     'word_id': self.word_id},
                    {'attribute_id': 8,
                     'attrkey': 'third_person_singular',
                     'attrvalue': None,
                     'quiz_id': 4,
                     'word': self.word,
                     'word_id': self.word_id},
                    {'attribute_id': 9,
                     'attrkey': 'first_person_plural',
                     'attrvalue': None,
                     'quiz_id': 4,
                     'word': self.word,
                     'word_id': self.word_id},
                    {'attribute_id': 10,
                     'attrkey': 'second_person_plural',
                     'attrvalue': 'second_person_plural',
                     'quiz_id': 4,
                     'word': self.word,
                     'word_id': self.word_id},
                    {'attribute_id': 11,
                     'attrkey': 'third_person_plural',
                     'attrvalue': 'third_person_plural',
                     'quiz_id': 4,
                     'word': self.word,
                     'word_id': self.word_id}]

        self.assertCountEqual(expected, obj)

    # use a valid quiz key but one that won't return anything:  genders for a verb
    def test_nonmatching_quiz_key(self):
        url = url_for('api_quiz.get_all_attr_values_for_quiz',
                      quiz_key='genders', word_id=self.word_id, _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    def test_undefined_quiz_key(self):
        url = url_for('api_quiz.get_all_attr_values_for_quiz',
                      quiz_key=''.join(random.choices(string.ascii_lowercase, k=10)),
                      word_id=self.word_id, _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    def test_undefined_word_id(self):
        url = url_for('api_quiz.get_all_attr_values_for_quiz',
                      quiz_key=self.QUIZ_KEY,
                      word_id=111111111,
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)
