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

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        wordlist_id_1 = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id_1)

        list_name_2 = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name_2
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        wordlist_id_2 = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id_2)

        delete_these = [wordlist_id_1, wordlist_id_2]

        r = self.client.put(url_for('api_wordlists.delete_wordlists', _external=True), json=delete_these)
        self.assertEqual(r.status_code, 200)

        # make sure they are gone
        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id_1, _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id_2, _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    def test_batch_delete_nothing(self):
        r = self.client.put(url_for('api_wordlists.delete_wordlists', _external=True), json=[])
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

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    # the setup for this class creates a list with just a name.
    # no tearDown method is needed thanks to our friend addCleanup
    def setUp(self):
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist_id)

        self.contents_update_url = url_for('api_wordlist.update_wordlist_contents', wordlist_id=self.wordlist_id,
                                           _external=True)
        self.wordlist_get_url = url_for('api_wordlist.get_wordlist', wordlist_id=self.wordlist_id,
                                        _external=True)
        self.metadata_update_url = url_for('api_wordlist.update_wordlist_metadata', wordlist_id=self.wordlist_id,
                                           _external=True)

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # add list with everything, incl. known and unknown words
    def test_create_dumb_list(self):
        payload = {
            'words': [
                'werfen',  # known
                'natehdnaoehu'  # unknown, hopefully
            ],
            'notes': 'important notes'
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)

        r = self.client.get(self.wordlist_get_url)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

    # add word to list
    def test_add_words_to_list(self):
        gibberish = 'aoeunhatedu'
        payload = {
            'words': [
                'werfen',
                'geben',
                gibberish
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)

        payload = {
            'words': [
                'wecken',
                'werfen',  # already there, should be a noop
                'nachgebend',
                gibberish
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        known_words = {x['word'] for x in obj['known_words']}
        unknown_words = {x for x in obj['unknown_words']}

        self.assertEqual(4, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))

        self.assertEqual({'wecken', 'nachgebend', 'geben', 'werfen'}, known_words)
        self.assertEqual({gibberish}, unknown_words)

    # update list with empty payload --> noop
    def test_update_contents_empty_payload(self):
        metadata_payload = {
            'sqlcode': """select id word_id from word where word = 'geben'"""
        }

        r = self.client.put(self.metadata_update_url, json=metadata_payload)
        self.assertEqual(r.status_code, 200)

        update_payload = {
        }

        r = self.client.put(self.contents_update_url, json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = self.client.get(self.wordlist_get_url)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        for k in metadata_payload.keys():
            self.assertEqual(metadata_payload[k], obj[k])

        self.assertTrue(len(obj['known_words']) > 0)

    # remove word by word from list -> removes from unknown
    def test_remove_word_by_word(self):
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            'words': [
                'werfen',  # known
                gibberish  # unknown, hopefully
            ],
            'notes': 'important notes'
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertTrue(len(obj['unknown_words']) > 0)
        word = obj['unknown_words'][0]
        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=self.wordlist_id, _external=True)
        r = self.client.post(url, json={
            "unknown_words": [word]
        })

        self.assertEqual(r.status_code, 200)

        r = self.client.get(self.wordlist_get_url)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

    # add an unknown word containing whitespace - should not succeed.  this case broke the UI
    def test_bad_unknown_word(self):
        garbage = 'bad dog %s' % ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            'words': [
                garbage
            ]
        }

        r_put = self.client.put(self.contents_update_url, json=payload)
        # should be a 400, which means that the payload did not pass validation.  anything else is a problem.
        self.assertEqual(r_put.status_code, 400)

        # make sure the garbage word didn't get added
        r_get = self.client.get(self.wordlist_get_url)
        self.assertEqual(r_get.status_code, 200)
        obj = json.loads(r_get.data)
        self.assertEqual('empty', obj['list_type'])

    # remove word by id from list
    def test_remove_word_by_id(self):
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            'words': [
                'werfen',  # known
                gibberish  # unknown, hopefully
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertTrue(len(obj['known_words']) > 0)
        word_id = obj['known_words'][0]['word_id']
        payload = {
            "word_ids": [word_id]
        }
        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=self.wordlist_id, _external=True)
        r = self.client.post(url, json=payload)
        self.assertEqual(r.status_code, 200)

        r = self.client.get(self.wordlist_get_url)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(0, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

    # update list with notes as empty string
    def test_update_notes_to_empty_string(self):
        payload = {
            'notes': ''
        }
        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)

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
        self.assertEqual(r.status_code, 200)

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
            'words': [
                'one',
                'two',
                'aoeuao'
            ]
        }
        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)

        # make sure the notes were unaffected

        r = self.client.get(self.wordlist_get_url)
        result = json.loads(r.data)
        self.assertEqual(notes, result['notes'])

    # add code to dumb list --> not allowed if list has words
    def test_add_code_to_dumb_list(self):
        # not allowed
        add_payload = {
            'words': [
                'werfen',
                'aoeuaoeu'
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
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(400, r.status_code)

    # get with bullshit wordlist id
    def test_get_bullshit_wordlist_id(self):
        url = url_for('api_wordlist.get_wordlist', wordlist_id=6666666, _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    # tests for changing list type; many cases

    # change list type: create empty, change to standard
    def test_change_list_type_empty_to_standard(self):
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))

        update_payload = {
            'words': [
                'werfen',
                gibberish
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
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            'words': [
                'werfen',
                gibberish
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual('standard', obj['list_type'])
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual(1, len(obj['known_words']))

        # remove the words
        word = obj['unknown_words'][0]
        word_id = obj['known_words'][0]['word_id']
        payload = {
            "word_ids": [word_id],
            "unknown_words": [word]
        }
        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=self.wordlist_id, _external=True)
        r = self.client.post(url, json=payload)
        self.assertEqual(r.status_code, 200)

        r = self.client.get(self.wordlist_get_url)
        obj = json.loads(r.data)

        self.assertEqual('empty', obj['list_type'])
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual(0, len(obj['known_words']))

    # removing words from a smart list should not be possible.  let's verify that.
    def test_remove_words_from_smart_list(self):
        payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual('smart', obj['list_type'])

        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=self.wordlist_id, _external=True)

        r = self.client.post(url, json={
            "word_ids": [66666],
        })

        self.assertNotEqual(200, r.status_code)

        r = self.client.post(url, json={
            "unknown_words": [66666],
        })

        self.assertNotEqual(200, r.status_code)


# tests for adding words by id
class APIWordlistAddByID(unittest.TestCase):
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

        # create a word
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
        }
        r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, self.word_id)

        self.metadata_update_url = url_for('api_wordlist.update_wordlist_metadata',
                                           wordlist_id=self.wordlist_id,
                                           _external=True)

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # base case, add word ids to a list.
    def test_add_by_word_id(self):
        # make sure the list is empty
        r = self.client.get(url_for('api_wordlist.get_wordlist', wordlist_id=self.wordlist_id,
                                    _external=True))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj['known_words']))

        # add the word by id
        r = self.client.put(url_for('api_wordlist.add_words_by_id',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json=[self.word_id])
        self.assertEqual(200, r.status_code)

        # make sure the list now has our word in it.
        r = self.client.get(url_for('api_wordlist.get_wordlist', wordlist_id=self.wordlist_id,
                                    _external=True))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(1, len(obj['known_words']))

    # add the same ids multiple times, should do no harm
    def test_add_by_word_id_repeat(self):
        # add the word by id
        r = self.client.put(url_for('api_wordlist.add_words_by_id',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json=[self.word_id])
        self.assertEqual(200, r.status_code)

        # add it again.
        r = self.client.put(url_for('api_wordlist.add_words_by_id',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json=[self.word_id])
        self.assertEqual(200, r.status_code)

        # make sure the list now has our word in it exactly once.
        r = self.client.get(url_for('api_wordlist.get_wordlist', wordlist_id=self.wordlist_id,
                                    _external=True))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(1, len(obj['known_words']))

    # add with empty payload
    def test_add_by_word_id_empty_payload(self):
        r = self.client.put(url_for('api_wordlist.add_words_by_id',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json=[])
        self.assertEqual(200, r.status_code)

    # add to smart list - should fail
    def test_add_by_word_id_smart_list(self):
        payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual('smart', obj['list_type'])

        # add the word by id - should not succeed
        r = self.client.put(url_for('api_wordlist.add_words_by_id',
                                    wordlist_id=self.wordlist_id, _external=True),
                            json=[self.word_id])
        self.assertEqual(400, r.status_code)

    # # add with bullshit wordlist_id - won't work because view function uses insert ignore
    # def test_add_by_word_id_bullshit_wordlist(self):
    #     r = self.client.put(url_for('api_wordlist.add_words_by_id',
    #                                 wordlist_id=self.wordlist_id, _external=True),
    #                         json=[6666666])
    #     self.assertNotEqual(200, r.status_code)
    #
    # # add with bullshit word_id - won't work because view function uses insert ignore
    # def test_add_by_word_id_bullshit_word_id(self):
    #     raise NotImplementedError(self.id())


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

        r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings', _external=True))
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

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        obj = json.loads(r.data)
        self.wordlist1_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, self.wordlist1_id)

        self.list_name_2 = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name_2
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
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
                                    wordlist_id=self.wordlist1_id, _external=True),
                            json={
                                "words": [self.word1, self.word2]
                            })
        self.assertEqual(200, r.status_code)

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents',
                                    wordlist_id=self.wordlist2_id, _external=True),
                            json={
                                "words": [self.word2, self.word3]
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
                                    wordlist_id=[self.wordlist1_id, self.wordlist2_id],
                                    _external=True))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = [self.word1_id, self.word2_id, self.word3_id]
        test = obj['word_ids']

        self.assertCountEqual(control, test)

    def test2(self):
        # in list 1, give one word two tags, then fetch with both tags.  verify correctness of result.
        r = self.client.post(url_for('api_wordlist_tag.add_tags',
                                     wordlist_id=self.wordlist1_id,
                                     word_id=self.word1_id,
                                     _external=True),
                             json=['tag1', 'tag2'])
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_wordlist.get_word_ids_from_wordlists',
                                    wordlist_id=[self.wordlist1_id],
                                    tag=['tag1', 'tag2'],
                                    _external=True))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = [self.word1_id]
        test = obj['word_ids']
        self.assertCountEqual(control, test)

    def test3(self):
        # correct behavior if fetching by tags with multiple list ids.
        r = self.client.get(url_for('api_wordlist.get_word_ids_from_wordlists',
                                    wordlist_id=[self.wordlist1_id, self.wordlist2_id],
                                    tag=['tag1', 'tag2'],
                                    _external=True))
        self.assertEqual(400, r.status_code)

    def test4(self):
        # fetch whole damn dictionary.
        r = self.client.get(url_for('api_wordlist.get_word_ids_from_wordlists',
                                    _external=True))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertLess(0, len(obj['word_ids']))
