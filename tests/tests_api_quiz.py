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

        # add the word to the list
        payload = {
            'words': [
                self.word
            ]
        }

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist_id,
                                    _external=True),
                            json=payload)

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # see if we fetch the word in the wordlist when using the api correctly
    def test_basic(self):
        # get_word_to_test returns one attribute value for a word, and unfortunately, when a quiz has multiple
        # attributes, we don't know which one.
        url = url_for('api_quiz.get_word_to_test',
                      quiz_key=self.QUIZ_KEY,
                      wordlist_id=[self.wordlist_id],
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(1, len(obj))

    # use a valid quiz key but one that won't return anything:  genders for a verb
    def test_nonmatching_quiz_key(self):
        url = url_for('api_quiz.get_word_to_test',
                      quiz_key='genders',
                      wordlist_id=[self.wordlist_id],
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    def test_undefined_quiz_key(self):
        url = url_for('api_quiz.get_word_to_test',
                      quiz_key=''.join(random.choices(string.ascii_lowercase, k=11)),
                      wordlist_id=[self.wordlist_id],
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    # should return something from the complete dictionary
    def test_no_wordlist(self):
        url = url_for('api_quiz.get_word_to_test',
                      quiz_key=self.QUIZ_KEY,
                      wordlist_id=None,
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(1, len(obj))

    def test_undefined_query(self):
        url = url_for('api_quiz.get_word_to_test',
                      quiz_key=self.QUIZ_KEY,
                      query=''.join(random.choices(string.ascii_lowercase, k=11)),
                      wordlist_id=[self.wordlist_id],
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(400, r.status_code)

    def test_empty_wordlist(self):
        # create an empty wordlist
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id)

        url = url_for('api_quiz.get_word_to_test',
                      quiz_key=self.QUIZ_KEY,
                      wordlist_id=[wordlist_id],
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    def test_undefined_wordlist(self):
        url = url_for('api_quiz.get_word_to_test',
                      quiz_key=self.QUIZ_KEY,
                      wordlist_id=[111111111],
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)


class APIQuizGetWordToTestSingleWordlist(unittest.TestCase):
    # unit tests for api_quiz.get_word_to_test_single_wordlist, which lets us search by tags.  this api call will
    # return an array of QUIZ_RESPONSE_SCHEMA
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
        # create a wordlist with two fake verbs, and tag one of them.  don't set all of their attributes
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist_id)

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

        self.word_1 = ''.join(random.choices(string.ascii_lowercase, k=11))
        add_payload = {
            "word": self.word_1,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['verb'],
            js.ATTRIBUTES: attributes
        }

        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.word_id_1 = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, self.word_id_1)

        self.word_2 = ''.join(random.choices(string.ascii_lowercase, k=11))
        add_payload = {
            "word": self.word_2,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['verb'],
            js.ATTRIBUTES: attributes
        }

        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.word_id_2 = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, self.word_id_2)

        # add the words to the list
        payload = {
            'words': [
                self.word_1,
                self.word_2
            ]
        }

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist_id,
                                    _external=True),
                            json=payload)

        # tag word_1
        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=self.wordlist_id,
                                     word_id=self.word_id_1,
                                     _external=True),
                             json=['tag1'])
        self.assertEqual(200, r.status_code)

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # see if we fetch the word in the wordlist when using the api correctly
    def test_basic_with_tag(self):
        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      tag=['tag1'],
                      wordlist_id=self.wordlist_id,
                      quiz_key=self.QUIZ_KEY,
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(1, len(obj))

    # see if we fetch both words in the wordlist when using the api correctly
    def test_basic_without_tag(self):
        # the way the api is implemented, we will get an attribute from either one of the words, not necessarily the
        # untagged one.
        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      wordlist_id=self.wordlist_id,
                      quiz_key=self.QUIZ_KEY,
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(1, len(obj))

    # use a valid quiz key but one that won't return anything:  genders for a verb
    def test_nonmatching_quiz_key(self):
        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      tag=['tag1'],
                      wordlist_id=self.wordlist_id,
                      quiz_key='genders',
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    def test_undefined_quiz_key(self):
        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      tag=['tag1'],
                      wordlist_id=self.wordlist_id,
                      quiz_key=''.join(random.choices(string.ascii_lowercase, k=10)),
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    def test_undefined_query(self):
        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      wordlist_id=self.wordlist_id,
                      quiz_key=self.QUIZ_KEY,
                      query=''.join(random.choices(string.ascii_lowercase, k=10)),
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(400, r.status_code)

    def test_undefined_wordlist(self):
        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      wordlist_id=111111111,
                      quiz_key=self.QUIZ_KEY,
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    def test_undefined_tag(self):
        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      tag=[''.join(random.choices(string.ascii_lowercase, k=10))],
                      wordlist_id=self.wordlist_id,
                      quiz_key=self.QUIZ_KEY,
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    def test_empty_wordlist(self):
        # create an empty wordlist
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        obj = json.loads(r.data)
        wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id)

        url = url_for('api_quiz.get_word_to_test_single_wordlist',
                      quiz_key=self.QUIZ_KEY,
                      wordlist_id=wordlist_id,
                      _external=True)
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))


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
        # create a fake verb, but don't set all of the attributes
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

    # do nothing, just make sure that setUp works
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
