import unittest
from dlernen import create_app
from flask import url_for
import json
import random
import string
from pprint import pprint


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id))


def cleanupWordlistID(client, wordlist_id):
    client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id))


class APIWordlistTagMultiList(unittest.TestCase):
    # tests for changes in the tagging api.  we can get words with a given tag from multiple lists,
    # and delete a given tag from multiple lists.

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

    def createWordlist(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        wordlist_id = obj['wordlist_id']

        return list_name, wordlist_id

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

    def assignWordAndTags(self, wordlist_id, word_id, tags):
        payload = {
            'word_ids': [
                word_id
            ]
        }

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents', wordlist_id=wordlist_id), json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=wordlist_id,
                                     word_id=word_id),
                             json=tags)
        self.assertEqual(201, r.status_code)

    def setUp(self):
        # create multiple word lists and dictionary entries.
        #
        # list0:  empty
        # list1:  word1 (tag1)
        # list2:  word2 (tag1)
        # list3:  word3 (tag1), word1 (tag1, tag2)
        #

        ############################
        #
        # create the lists
        #
        ############################

        list_name_0, self.wordlist0_id = self.createWordlist()  # we'll keep this empty
        list_name_1, self.wordlist1_id = self.createWordlist()
        list_name_2, self.wordlist2_id = self.createWordlist()
        list_name_3, self.wordlist3_id = self.createWordlist()

        self.addCleanup(cleanupWordlistID, self.client, self.wordlist0_id)
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist1_id)
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist2_id)
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist3_id)

        ############################
        #
        # create the words
        #
        ############################

        self.word1, self.word1_id = self.createWord()
        self.word2, self.word2_id = self.createWord()
        self.word3, self.word3_id = self.createWord()

        self.addCleanup(cleanupWordID, self.client, self.word1_id)
        self.addCleanup(cleanupWordID, self.client, self.word2_id)
        self.addCleanup(cleanupWordID, self.client, self.word3_id)

        ############################
        #
        # assign words to lists and tags to words
        #
        ############################

        self.assignWordAndTags(self.wordlist1_id, self.word1_id, ['tag1'])
        self.assignWordAndTags(self.wordlist2_id, self.word2_id, ['tag1'])
        self.assignWordAndTags(self.wordlist3_id, self.word3_id, ['tag1'])
        self.assignWordAndTags(self.wordlist3_id, self.word1_id, ['tag1', 'tag2'])

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # test cases:
    #
    # get_words with no filtering - retrieves whole dictionary.
    def test1(self):
        r = self.client.get(url_for('api_words.get_words'))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertGreater(len(obj), 1000)

    # get_words, filter just by tags.
    def test2(self):
        r = self.client.get(url_for('api_words.get_words', tag=['tag1']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        # should retrieve word1 and word3
        control = [self.word1_id, self.word2_id, self.word3_id]
        experiment = [x['word_id'] for x in obj]

        self.assertCountEqual(control, experiment)

    # filter with multiple tags
    def test2_5(self):
        r = self.client.get(url_for('api_words.get_words', tag=['tag1', 'tag2']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = [self.word1_id, self.word2_id, self.word3_id]
        experiment = [x['word_id'] for x in obj]

        self.assertCountEqual(control, experiment)

    # get_words, filter just by wordlist_ids
    def test3(self):
        r = self.client.get(url_for('api_words.get_words', wordlist_id=[self.wordlist1_id, self.wordlist3_id]))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        # should retrieve word1 and word3
        control = [self.word1_id, self.word3_id]
        experiment = [x['word_id'] for x in obj]

        self.assertCountEqual(control, experiment)

    # get_words, filter by both.  there should be a test that shows 0 results with the given parameters.
    def test4(self):
        r = self.client.get(url_for('api_words.get_words',
                                    wordlist_id=[self.wordlist3_id],
                                    tag=['tag2']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = [self.word1_id]
        experiment = [x['word_id'] for x in obj]

        self.assertCountEqual(control, experiment)

    def test4_5(self):
        r = self.client.get(url_for('api_words.get_words',
                                    wordlist_id=[self.wordlist3_id],
                                    tag=['tag1', 'tag2']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = [self.word1_id, self.word3_id]
        experiment = [x['word_id'] for x in obj]

        self.assertCountEqual(control, experiment)

    def test4_6(self):
        r = self.client.get(url_for('api_words.get_words',
                                    wordlist_id=[self.wordlist2_id, self.wordlist3_id],
                                    tag=['no_such_tag']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    def test4_7(self):
        r = self.client.get(url_for('api_words.get_words',
                                    wordlist_id=[self.wordlist1_id],
                                    tag=['tag2']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    # delete a tag from all wordlists.  to verify, retrieve by the tag and ensure that it's not found
    def test5(self):
        r = self.client.get(url_for('api_words.get_words', tag=['tag1']))
        self.assertEqual(200, r.status_code)

        r = self.client.delete(url_for('api_wordlist_tag.delete_tag', tag='tag1'))
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_words.get_words', tag=['tag1']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    # delete a tag from specific word lists
    def test6(self):
        r = self.client.get(url_for('api_words.get_words',
                                    wordlist_id=[self.wordlist1_id],
                                    tag=['tag1']))
        self.assertEqual(200, r.status_code)

        r = self.client.delete(url_for('api_wordlist_tag.delete_tag',
                                       wordlist_id=[self.wordlist1_id],
                                       tag='tag1'))
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_words.get_words',
                                    wordlist_id=[self.wordlist1_id],
                                    tag=['tag1']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

        r = self.client.get(url_for('api_words.get_words',
                                    wordlist_id=[self.wordlist2_id],
                                    tag=['tag1']))
        self.assertEqual(200, r.status_code)

    # TODO need tests for smart lists!


class APIWordlistTagSmartList(unittest.TestCase):
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
            r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings'))
            cls.keyword_mappings = json.loads(r.data)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def setUp(self):
        # create two dictionary entries
        self.word1 = "word1_" + ''.join(random.choices(string.ascii_lowercase, k=10))
        self.word2 = "word2_" + ''.join(random.choices(string.ascii_lowercase, k=10))

        add_payload = {
            "word": self.word1,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.word1_id = obj['word_id']

        add_payload = {
            "word": self.word2,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.word2_id = obj['word_id']

        self.addCleanup(cleanupWordID, self.client, self.word1_id)
        self.addCleanup(cleanupWordID, self.client, self.word2_id)

        # create a smart list.  the SQL will be set up so that word1 is in the list but word2 is not.
        sql = "select id word_id from word where word = '%s'" % self.word1

        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name,
            'sqlcode': sql
        }

        url = url_for('api_wordlist.create_wordlist_metadata')

        r = self.client.post(url, json=add_payload)
        obj = json.loads(r.data)
        self.wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist_id)

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        r = self.client.get(url_for('api_wordlist.get_wordlist',
                                    wordlist_id=self.wordlist_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(1, len(obj['words']))
        self.assertEqual(self.word1_id, obj['words'][0]['word_id'])

    def test_addTags(self):
        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=self.wordlist_id,
                                     word_id=self.word1_id),
                             json=['tag1', 'tag2'])
        self.assertNotEqual(201, r.status_code)

    def test_deleteTags(self):
        r = self.client.delete(url_for('api_wordlist_tag.delete_tags_for_word_id',
                                       wordlist_id=self.wordlist_id,
                                       word_id=self.word1_id),
                               json=['tag1', 'tag2'])
        self.assertNotEqual(200, r.status_code)

    def test_get_nonmember(self):
        r = self.client.get(url_for('api_wordlist_tag.get_tags',
                                    wordlist_id=self.wordlist_id,
                                    word_id=self.word2_id))
        self.assertEqual(404, r.status_code)

    def test_get_member(self):
        r = self.client.get(url_for('api_wordlist_tag.get_tags',
                                    wordlist_id=self.wordlist_id,
                                    word_id=self.word1_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj['tags']))


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
            r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings'))
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

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=add_payload)
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
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.word1_id = obj['word_id']

        add_payload = {
            "word": self.word2,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.word2_id = obj['word_id']

        add_payload = {
            "word": self.word3,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.word3_id = obj['word_id']

        self.addCleanup(cleanupWordID, self.client, self.word1_id)
        self.addCleanup(cleanupWordID, self.client, self.word2_id)
        self.addCleanup(cleanupWordID, self.client, self.word3_id)

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist_id),
                            json={
                                "word_ids": [self.word1_id, self.word2_id, self.word3_id]
                            })
        self.assertEqual(200, r.status_code)

        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=self.wordlist_id,
                                     word_id=self.word2_id),
                             json=['tag1', 'tag2'])
        self.assertEqual(201, r.status_code)

        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=self.wordlist_id,
                                     word_id=self.word3_id),
                             json=['tag1'])
        self.assertEqual(201, r.status_code)

    # ################################
    # there is no tearDown method (we do have tearDownClass).  addCleanup takes care of housekeeping.
    # ################################

    # do nothing, just make sure that setUp works
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

    # 1. GET /api/wordlist/<int:wordlist_id>
    def test1(self):
        r = self.client.get(url_for('api_wordlist.get_wordlist', wordlist_id=self.wordlist_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(3, len(obj['words']))

        # check that the word ids in the result are what we think they are
        control_word_ids = [self.word1_id, self.word2_id, self.word3_id]
        test_word_ids = [x['word_id'] for x in obj['words']]
        self.assertCountEqual(control_word_ids, test_word_ids)

        # check that the words have the correct tags
        test_dict = {x['word']: x['tags'] for x in obj['words']}
        control_dict = {
            self.word1: [],
            self.word2: ['tag2', 'tag1'],
            self.word3: ['tag1']
        }

        self.assertCountEqual(control_dict[self.word1], test_dict[self.word1])
        self.assertCountEqual(control_dict[self.word2], test_dict[self.word2])
        self.assertCountEqual(control_dict[self.word3], test_dict[self.word3])

    # 2. GET /api/wordlist/<int:wordlist_id>?tag=tag1
    def test2(self):
        r = self.client.get(url_for('api_wordlist.get_wordlist',
                                    wordlist_id=self.wordlist_id,
                                    tag=['tag1']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(2, len(obj['words']))

        # check that the word ids in the result are what we think they are
        control_word_ids = [self.word2_id, self.word3_id]
        test_word_ids = [x['word_id'] for x in obj['words']]
        self.assertCountEqual(control_word_ids, test_word_ids)

        # check that the words have the correct tags
        test_dict = {x['word']: x['tags'] for x in obj['words']}
        control_dict = {
            self.word2: ['tag1'],
            self.word3: ['tag1']
        }

        self.assertCountEqual(control_dict[self.word2], test_dict[self.word2])
        self.assertCountEqual(control_dict[self.word3], test_dict[self.word3])

    # 3. GET /api/wordlist/<int:wordlist_id>?tag=tag2
    def test3(self):
        r = self.client.get(url_for('api_wordlist.get_wordlist',
                                    wordlist_id=self.wordlist_id,
                                    tag=['tag2']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(1, len(obj['words']))

        # check that the word ids in the result are what we think they are
        control_word_ids = [self.word2_id]
        test_word_ids = [x['word_id'] for x in obj['words']]
        self.assertCountEqual(control_word_ids, test_word_ids)

        # check that the words have the correct tags
        test_dict = {x['word']: x['tags'] for x in obj['words']}
        control_dict = {
            self.word2: ['tag2']
        }

        self.assertCountEqual(control_dict[self.word2], test_dict[self.word2])

    # 4. GET /api/wordlist/<int:wordlist_id>?tag=tag1&tag=tag2
    def test4(self):
        r = self.client.get(url_for('api_wordlist.get_wordlist',
                                    wordlist_id=self.wordlist_id,
                                    tag=['tag1', 'tag2']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(2, len(obj['words']))

        # check that the word ids in the result are what we think they are
        control_word_ids = [self.word3_id, self.word2_id]
        test_word_ids = [x['word_id'] for x in obj['words']]
        self.assertCountEqual(control_word_ids, test_word_ids)

        # check that the words have the correct tags
        test_dict = {x['word']: x['tags'] for x in obj['words']}
        control_dict = {
            self.word2: ['tag2', 'tag1'],
            self.word3: ['tag1']
        }

        self.assertCountEqual(control_dict[self.word2], test_dict[self.word2])

    # 5. GET /api/wordlist/<int:wordlist_id>?tag=tag2&tag=tag2  # i.e. duplicate tag
    def test5(self):
        r = self.client.get(url_for('api_wordlist.get_wordlist',
                                    wordlist_id=self.wordlist_id,
                                    tag=['tag2', 'tag2']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(1, len(obj['words']))

        # check that the word ids in the result are what we think they are
        control_word_ids = [self.word2_id]
        test_word_ids = [x['word_id'] for x in obj['words']]
        self.assertCountEqual(control_word_ids, test_word_ids)

        # check that the words have the correct tags
        test_dict = {x['word']: x['tags'] for x in obj['words']}
        control_dict = {
            self.word2: ['tag2']
        }

        self.assertCountEqual(control_dict[self.word2], test_dict[self.word2])

    # 6. GET /api/wordlist/<int:wordlist_id>?tag=bullshit       # should return nothing
    def test6(self):
        r = self.client.get(url_for('api_wordlist.get_wordlist',
                                    wordlist_id=self.wordlist_id,
                                    tag=['bullshit']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(0, len(obj['words']))
