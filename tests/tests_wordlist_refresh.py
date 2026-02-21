import unittest
from dlernen import create_app
from flask import url_for
import json
import random
import string
from pprint import pprint


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id, _external=True))


def cleanupWordlistID(client, wordlist_id):
    client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id, _external=True))


class TestWordlistRefresh(unittest.TestCase):
    # ensure correct behavior of list updates when words are added to the dictionary.

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

        r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings', _external=True))
        cls.keyword_mappings = json.loads(r.data)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    # the setup for this class creates a list with just a name.
    def setUp(self):
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist_id)

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    # adding an unknown word to a list is idempotent.
    def test_idempotent(self):
        # add a garbage word to the class wordlist; should wind up in the unknown list.
        word = ''.join(random.choices(string.ascii_lowercase, k=10))

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json={
                                "words": [word]
                            })
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual(word, obj['unknown_words'][0])

        # add it again.  nothing should change.
        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json={
                                "words": [word]
                            })
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual(word, obj['unknown_words'][0])

    # wordlists are updated when words are added.
    def test_basic(self):
        # add a garbage word to the class wordlist; should wind up in the unknown list.
        word = ''.join(random.choices(string.ascii_lowercase, k=10))

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json={
                                "words": [word]
                            })
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual(word, obj['unknown_words'][0])

        # create a dictionary entry for the garbage word.

        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        # check that the wordlist has been updated:  the garbage word should be moved
        # to the known words.
        r = self.client.get(url_for('api_wordlist.get_wordlist',
                                    wordlist_id=self.wordlist_id, _external=True))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual(word, obj['known_words'][0]['word'])

    # adding a known word to a wordlist
    def test_add_known_word(self):
        # create a garbage word and make a dictionary entry for it.
        word = ''.join(random.choices(string.ascii_lowercase, k=10))

        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        # then put it into the list.  it should be among the known words.
        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json={
                                "words": [word]
                            })
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual(word, obj['known_words'][0]['word'])

    # adding by word id?