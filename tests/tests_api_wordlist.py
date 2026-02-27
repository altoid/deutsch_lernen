import unittest
from dlernen import create_app, dlernen_json_schema as js
from flask import url_for
import json
import random
import string
from pprint import pprint


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id))


def cleanupWordlistID(client, wordlist_id):
    client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id))


class APIWordlistBatchDelete(unittest.TestCase):
    # need a separate class for this because we don't want setUp/tearDown methods here.
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

    # do nothing, just make sure that setUpClass and tearDownClaass work
    def test_nothing(self):
        pass

    def test_batch_delete(self):
        # create two lists, delete them in one request, make sure they are gone.
        list_name_1 = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name_1
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        wordlist_id_1 = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id_1)

        list_name_2 = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name_2
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        wordlist_id_2 = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id_2)

        delete_these = [wordlist_id_1, wordlist_id_2]

        r = self.client.put(url_for('api_wordlists.delete_wordlists'), json=delete_these)
        self.assertEqual(r.status_code, 200)

        # make sure they are gone
        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id_1)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id_2)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    def test_batch_delete_nothing(self):
        r = self.client.put(url_for('api_wordlists.delete_wordlists'), json=[])
        self.assertEqual(r.status_code, 200)


class APIWordlist(unittest.TestCase):
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

    # the setup for this class creates a list with just a name.
    # no tearDown method is needed thanks to our friend addCleanup
    def setUp(self):
        self.list_name, self.wordlist_id = self.createWordlist()
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist_id)

        self.word1, self.word1_id = self.createWord()
        self.addCleanup(cleanupWordID, self.client, self.word1_id)

        self.word2, self.word2_id = self.createWord()
        self.addCleanup(cleanupWordID, self.client, self.word2_id)

        self.contents_update_url = url_for('api_wordlist.update_wordlist_contents', wordlist_id=self.wordlist_id)
        self.wordlist_get_url = url_for('api_wordlist.get_wordlist', wordlist_id=self.wordlist_id)
        self.metadata_update_url = url_for('api_wordlist.update_wordlist_metadata', wordlist_id=self.wordlist_id)

    # do nothing, just make sure that setUp works (by creating an empty list)
    def test_nothing(self):
        r = self.client.get(self.wordlist_get_url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual('empty', obj['list_type'])

    # test basic add - in one request, add everything we can add in a single request
    def test_create_dumb_list(self):
        payload = {
            'word_ids': [
                self.word1_id
            ],
            'notes': 'important notes'
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(self.wordlist_get_url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(1, len(obj['words']))
        self.assertEqual('standard', obj['list_type'])

    # add word to list
    def test_add_words_to_list(self):
        payload = {
            'word_ids': [
                self.word1_id
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)

        payload = {
            'word_ids': [
                self.word1_id,  # already there, should be a noop
                self.word2_id
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = {self.word1, self.word2}
        experiment = {x['word'] for x in obj['words']}

        self.assertCountEqual(control, experiment)

    # update list with empty payload --> noop
    def test_update_contents_empty_payload(self):
        metadata_payload = {
            'sqlcode': """select id word_id from word where word = 'geben'"""
        }

        r = self.client.put(self.metadata_update_url, json=metadata_payload)
        self.assertEqual(200, r.status_code)

        update_payload = {
        }

        r = self.client.put(self.contents_update_url, json=update_payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(self.wordlist_get_url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        for k in metadata_payload.keys():
            self.assertEqual(metadata_payload[k], obj[k])

        self.assertTrue(len(obj['words']) > 0)

    def test_add_bad_word_id(self):
        payload = {
            'word_ids': self.word1_id * 2
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(400, r.status_code)

    # remove word by id from list
    def test_remove_word_by_id(self):
        payload = {
            'word_ids': [
                self.word1_id
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(1, len(obj['words']))

        payload = {
            "word_ids": [self.word1_id]
        }
        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=self.wordlist_id)
        r = self.client.post(url, json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(self.wordlist_get_url)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(0, len(obj['words']))
        self.assertEqual('empty', obj['list_type'])

    # update list with notes as empty string
    def test_update_notes_to_empty_string(self):
        payload = {
            'notes': ''
        }
        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)

        # make sure the notes were cleared

        r = self.client.get(self.wordlist_get_url)
        obj = json.loads(r.data)
        self.assertEqual('', obj['notes'])

    # update list with notes as None
    def test_update_notes_to_None(self):
        notes = 'euioeuiaoeuaoeu'
        payload = {
            'notes': notes
        }
        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(self.wordlist_get_url)
        obj = json.loads(r.data)
        self.assertEqual(notes, obj['notes'])

        # set notes to None - should succeed

        payload = {
            'notes': None
        }
        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)

        # make sure the notes were cleared

        r = self.client.get(self.wordlist_get_url)
        obj = json.loads(r.data)
        self.assertIsNone(obj['notes'])

    # update something other than the notes and make sure the notes didn't get bashed
    def test_update_does_not_affect_notes(self):
        notes = 'anhtoednaoehduntaeo'
        payload = {
            'notes': notes
        }
        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)

        # add some words then check the notes

        payload = {
            'word_ids': [
                self.word1_id,
                self.word2_id
            ]
        }
        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)

        # make sure the notes were unaffected

        r = self.client.get(self.wordlist_get_url)
        result = json.loads(r.data)
        self.assertEqual(notes, result['notes'])

    # add code to dumb list --> not allowed if list has words
    def test_add_code_to_dumb_list(self):
        # not allowed
        add_payload = {
            'word_ids': [
                self.word1_id,
                self.word2_id
            ]
        }

        r = self.client.put(self.contents_update_url, json=add_payload)
        self.assertEqual(200, r.status_code)

        update_payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = self.client.put(self.metadata_update_url, json=update_payload)
        self.assertEqual(400, r.status_code)

    # add words to smart list --> not allowed.
    def test_add_words_to_smart_list(self):
        # not allowed
        payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual('smart', obj['list_type'])

        payload = {
            'word_ids': [
                self.word1_id,
                self.word2_id
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(400, r.status_code)

    # get with bullshit wordlist id
    def test_get_bullshit_wordlist_id(self):
        url = url_for('api_wordlist.get_wordlist', wordlist_id=6666666)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    # tests for changing list type; many cases

    # change list type: create empty, change to standard
    def test_change_list_type_empty_to_standard(self):

        update_payload = {
            'word_ids': [
                self.word1_id,
                self.word2_id
            ]
        }

        r = self.client.put(self.contents_update_url,
                            json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual('standard', obj['list_type'])

    # change list type: create smart, change to empty
    def test_change_list_type_smart_to_empty(self):
        payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual('smart', obj['list_type'])

        payload = {
            'sqlcode': None
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual('empty', obj['list_type'])

    # there is no test for create standard, change to smart
    # because this can't be done in one request.  we have to empty the list first
    # then change to smart.

    # change list type: create standard, change to empty
    def test_change_list_type_standard_to_empty(self):
        payload = {
            'word_ids': [
                self.word1_id,
                self.word2_id
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual('standard', obj['list_type'])
        self.assertEqual(2, len(obj['words']))

        # remove the words
        payload = {
            'word_ids': [
                self.word1_id,
                self.word2_id
            ]
        }
        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=self.wordlist_id)
        r = self.client.post(url, json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(self.wordlist_get_url)
        obj = json.loads(r.data)

        self.assertEqual('empty', obj['list_type'])
        self.assertEqual(0, len(obj['words']))

    # removing words from a smart list should not be possible.  let's verify that.
    def test_remove_words_from_smart_list(self):
        payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual('smart', obj['list_type'])

        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=self.wordlist_id)

        r = self.client.post(url, json={
            "word_ids": [self.word1_id],
        })

        self.assertNotEqual(200, r.status_code)


class APIWordlistGetWordIDs(unittest.TestCase):
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

    # the setup for this class creates two lists and two words.
    #
    # list1:  word1 word2
    # list2:        word2 word3
    #
    # i.e. one of the words is in both lists.
    def setUp(self):
        self.list_name_1 = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name_1
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=add_payload)
        obj = json.loads(r.data)
        self.wordlist1_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist1_id)

        self.list_name_2 = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name_2
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=add_payload)
        obj = json.loads(r.data)
        self.wordlist2_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist2_id)

        # create three words, add them to the lists as above.

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
                                    wordlist_id=self.wordlist1_id),
                            json={
                                "word_ids": [self.word1_id, self.word2_id]
                            })
        self.assertEqual(200, r.status_code)

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist2_id),
                            json={
                                "word_ids": [self.word2_id, self.word3_id]
                            })
        self.assertEqual(200, r.status_code)

    # ################################
    # there is no tearDown method (we do have tearDownClass).  addCleanup takes care of housekeeping.
    # ################################

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # verify correctness of returned list of word ids.
    def test1(self):
        r = self.client.get(url_for('api_wordlist.get_word_ids_from_wordlists',
                                    wordlist_id=[self.wordlist1_id, self.wordlist2_id]))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = [self.word1_id, self.word2_id, self.word3_id]
        test = obj['word_ids']

        self.assertCountEqual(control, test)

    def test2(self):
        # in list 1, give one word two tags, then fetch with both tags.  verify correctness of result.
        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=self.wordlist1_id,
                                     word_id=self.word1_id),
                             json=['tag1', 'tag2'])
        self.assertEqual(201, r.status_code)

        r = self.client.get(url_for('api_wordlist.get_word_ids_from_wordlists',
                                    wordlist_id=[self.wordlist1_id],
                                    tag=['tag1', 'tag2']))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = [self.word1_id]
        test = obj['word_ids']
        self.assertCountEqual(control, test)

    def test3(self):
        # correct behavior if fetching by tags with multiple list ids.
        r = self.client.get(url_for('api_wordlist.get_word_ids_from_wordlists',
                                    wordlist_id=[self.wordlist1_id, self.wordlist2_id],
                                    tag=['tag1', 'tag2']))
        self.assertEqual(400, r.status_code)

    def test4(self):
        # fetch whole damn dictionary.
        r = self.client.get(url_for('api_wordlist.get_word_ids_from_wordlists'))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertLess(0, len(obj['word_ids']))
