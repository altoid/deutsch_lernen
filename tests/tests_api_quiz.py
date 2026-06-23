import unittest
import random
import string
from dlernen import create_app
from dlernen.dlernen_json_schema import ATTRIBUTES
from flask import url_for
import json
from dlernen.api_pos import POSName
from pprint import pprint
from dlernen.api_quiz import Selector


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id))


def cleanupWordlistID(client, wordlist_id):
    client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id))


class APIQuizSelector(unittest.TestCase):
    # make sure dynamically-created Selector Enum class is well-behaved

    def test1(self):
        self.assertEqual('oldest_first', Selector.OLDEST_FIRST)

    def test2(self):
        self.assertTrue(Selector.OLDEST_FIRST, Selector.DEFAULT)

    def test3(self):
        self.assertTrue('rare' in Selector)

    def test4(self):
        self.assertTrue(Selector.RARE in Selector)


class APIPostQuizAnswer(unittest.TestCase):
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

    def create_adjective(self):
        # create a fake word with just a definition
        word = ''.join(random.choices(string.ascii_lowercase, k=11))
        attrkeys = [
            'definition',
        ]
        attributes = [
            {
                "attribute_id": self.keyword_mappings['attribute_names_to_ids'][k],
                "attrvalue": k,
            }
            for k in attrkeys
        ]
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids'][POSName.ADJECTIVE],
            ATTRIBUTES: attributes
        }

        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        obj = json.loads(r.data)
        word_id = obj['word_id']

        self.addCleanup(cleanupWordID, self.client, word_id)

        return word, word_id

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # make sure garbage payload does not pass validation
    def test_garbage_payload(self):
        payload = {
            'snaoteuh': 'bstaeohusa'
        }
        r = self.client.post(url_for('api_quiz.post_quiz_score', quiz_key='definitions'), json=payload)
        self.assertEqual(400, r.status_code)

    # test that posting a score works
    def test_basic(self):
        quiz_key = 'definitions'
        word, word_id = self.create_adjective()
        payload = {
            'word_id': word_id,
            'correct': True,
            'attribute_id': self.keyword_mappings['attribute_names_to_ids']['definition']
        }
        r = self.client.post(url_for('api_quiz.post_quiz_score', quiz_key=quiz_key), json=payload)
        self.assertEqual(201, r.status_code)

    # bad quiz_key
    def test1(self):
        quiz_key = 'euiaeuaoua'
        word, word_id = self.create_adjective()
        payload = {
            'word_id': word_id,
            'correct': True,
            'attribute_id': self.keyword_mappings['attribute_names_to_ids']['definition']
        }
        r = self.client.post(url_for('api_quiz.post_quiz_score', quiz_key=quiz_key), json=payload)
        self.assertEqual(400, r.status_code)

    # not a candidate
    def test2(self):
        quiz_key = 'present_indicative'
        word, word_id = self.create_adjective()
        payload = {
            'word_id': word_id,
            'correct': True,
            'attribute_id': self.keyword_mappings['attribute_names_to_ids']['first_person_singular']
        }
        r = self.client.post(url_for('api_quiz.post_quiz_score', quiz_key=quiz_key), json=payload)
        self.assertEqual(400, r.status_code)

    # invalid attribute
    def test3(self):
        quiz_key = 'definitions'
        word, word_id = self.create_adjective()
        payload = {
            'word_id': word_id,
            'correct': True,
            'attribute_id': self.keyword_mappings['attribute_names_to_ids']['first_person_singular']
        }
        r = self.client.post(url_for('api_quiz.post_quiz_score', quiz_key=quiz_key), json=payload)
        self.assertEqual(400, r.status_code)


class APIQuizTestGetSingleWord(unittest.TestCase):
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

        r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings'))
        cls.keyword_mappings = json.loads(r.data)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def create_adjective(self):
        # create a fake word with just a definition
        word = ''.join(random.choices(string.ascii_lowercase, k=11))
        attrkeys = [
            'definition',
        ]
        attributes = [
            {
                "attribute_id": self.keyword_mappings['attribute_names_to_ids'][k],
                "attrvalue": k,
            }
            for k in attrkeys
        ]
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids'][POSName.ADJECTIVE],
            ATTRIBUTES: attributes
        }

        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        obj = json.loads(r.data)
        word_id = obj['word_id']

        self.addCleanup(cleanupWordID, self.client, word_id)

        return word, word_id

    def create_incomplete_verb(self):
        # create a fake verb with just a definition
        word = ''.join(random.choices(string.ascii_lowercase, k=11))
        attrkeys = [
            'definition',
        ]
        attributes = [
            {
                "attribute_id": self.keyword_mappings['attribute_names_to_ids'][k],
                "attrvalue": k,
            }
            for k in attrkeys
        ]
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids'][POSName.VERB],
            ATTRIBUTES: attributes
        }

        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        obj = json.loads(r.data)
        word_id = obj['word_id']

        self.addCleanup(cleanupWordID, self.client, word_id)

        return word, word_id

    def create_complete_verb(self):
        # create a fake verb with all attributes set
        word = ''.join(random.choices(string.ascii_lowercase, k=11))
        attrkeys = [
            # these are all the attributes defined for the 'present_indicative' quiz
            'first_person_singular',
            'second_person_singular',
            'third_person_singular',
            'first_person_plural',
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
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids'][POSName.VERB],
            ATTRIBUTES: attributes
        }

        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        obj = json.loads(r.data)
        word_id = obj['word_id']

        self.addCleanup(cleanupWordID, self.client, word_id)

        return word, word_id

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # invalid quiz key -> 404
    def test1(self):
        quiz_key = 'bullshit'
        _, word_id = self.create_adjective()

        r = self.client.get(url_for('api_quiz.get_single_word',
                                    quiz_key=quiz_key,
                                    word_id=word_id))
        self.assertEqual(404, r.status_code)

    # invalid word id -> 404
    def test2(self):
        r = self.client.get(url_for('api_quiz.get_single_word',
                                    quiz_key=self.QUIZ_KEY,
                                    word_id=8675309))
        self.assertEqual(404, r.status_code)

    # word is not a candidate for the quiz -> 400
    def test3(self):
        _, word_id = self.create_adjective()

        r = self.client.get(url_for('api_quiz.get_single_word',
                                    quiz_key=self.QUIZ_KEY,
                                    word_id=word_id))
        self.assertEqual(400, r.status_code)

    # word is a candidate but not all of its attributes are there -> 409
    def test4(self):
        _, word_id = self.create_incomplete_verb()

        r = self.client.get(url_for('api_quiz.get_single_word',
                                    quiz_key=self.QUIZ_KEY,
                                    word_id=word_id))
        self.assertEqual(409, r.status_code)

    # finally, make all inputs valid to prove that we can get a 200!
    def test5(self):
        _, word_id = self.create_complete_verb()

        r = self.client.get(url_for('api_quiz.get_single_word',
                                    quiz_key=self.QUIZ_KEY,
                                    word_id=word_id))
        self.assertEqual(200, r.status_code)
