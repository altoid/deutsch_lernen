import unittest
from dlernen import create_app, dlernen_json_schema as js
from flask import url_for
import json
import random
import string
from pprint import pprint


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id, _external=True))


def cleanupWordlistID(client, wordlist_id):
    client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id, _external=True))


class APIWordlistTag(unittest.TestCase):
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

        with cls.app.test_request_context():
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

        # create three words, add them to the list, and tag them as follows:
        #
        # word1:  (no tags)
        # word2:  tag1 tag2
        # word3:  tag1

        self.word1 = "word1_" + ''.join(random.choices(string.ascii_lowercase, k=10))
        self.word2 = "word2_" + ''.join(random.choices(string.ascii_lowercase, k=10))
        self.word3 = "word3_" + ''.join(random.choices(string.ascii_lowercase, k=10))

        add_payload = {
            "word": self.word1,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.word1_id = obj['word_id']

        add_payload = {
            "word": self.word2,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.word2_id = obj['word_id']

        add_payload = {
            "word": self.word3,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.word3_id = obj['word_id']

        self.addCleanup(cleanupWordID, self.client, self.word1_id)
        self.addCleanup(cleanupWordID, self.client, self.word2_id)
        self.addCleanup(cleanupWordID, self.client, self.word3_id)

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json={
                                "words": [self.word1, self.word2, self.word3]
                            })
        self.assertEqual(200, r.status_code)

        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=self.wordlist_id,
                                     word_id=self.word2_id,
                                     _external=True),
                             json=['tag1', 'tag2'])
        self.assertEqual(200, r.status_code)

        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=self.wordlist_id,
                                     word_id=self.word3_id,
                                     _external=True),
                             json=['tag1'])
        self.assertEqual(200, r.status_code)

    # ################################
    # there is no tearDown method (we do have tearDownClass).  addCleanup takes care of housekeeping.
    # ################################

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    # test cases:
    #
    # 1. GET /api/wordlist/<int:wordlist_id>
    # 2. GET /api/wordlist/<int:wordlist_id>?tag=tag1
    # 3. GET /api/wordlist/<int:wordlist_id>?tag=tag2
    # 4. GET /api/wordlist/<int:wordlist_id>?tag=tag1&tag=tag2
    # 5. GET /api/wordlist/<int:wordlist_id>?tag=tag2&tag=tag2  # i.e. duplicate tag
    # 6. GET /api/wordlist/<int:wordlist_id>?tag=bullshit       # should return nothing

    def test1(self):
        r = self.client.get(url_for('api_wordlist.get_wordlist', wordlist_id=self.wordlist_id, _external=True))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

    def test2(self):
        raise NotImplementedError()

    def test3(self):
        raise NotImplementedError()

    def test4(self):
        raise NotImplementedError()

    def test5(self):
        raise NotImplementedError()

    def test6(self):
        raise NotImplementedError()
