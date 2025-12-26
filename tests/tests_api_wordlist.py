import unittest
from dlernen import create_app, dlernen_json_schema as js
from flask import url_for
import json
import random
import string
from pprint import pprint


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

        list_name_2 = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name_2
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        wordlist_id_2 = obj['wordlist_id']

        delete_these = [wordlist_id_1, wordlist_id_2]

        r = self.client.put(url_for('api_wordlist.delete_wordlists', _external=True), json=delete_these)
        self.assertEqual(r.status_code, 200)

        # make sure they are gone
        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id_1, _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id_2, _external=True)
        r = self.client.get(url)
        self.assertEqual(404, r.status_code)

    def test_batch_delete_nothing(self):
        r = self.client.put(url_for('api_wordlist.delete_wordlists', _external=True), json=[])
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
    def setUp(self):
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
            obj = json.loads(r.data)
            self.wordlist_id = obj['wordlist_id']

            self.contents_update_url = url_for('api_wordlist.update_wordlist_contents', wordlist_id=self.wordlist_id,
                                               _external=True)
            self.wordlist_get_url = url_for('api_wordlist.get_wordlist', wordlist_id=self.wordlist_id,
                                            _external=True)
            self.metadata_update_url = url_for('api_wordlist.update_wordlist_metadata', wordlist_id=self.wordlist_id,
                                               _external=True)

    def tearDown(self):
        with self.app.test_request_context():
            self.client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=self.wordlist_id,
                                       _external=True))

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    # add list with everything, incl. known and unknown words
    def test_create_dumb_list(self):
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
            url = url_for('api_wordlist.get_wordlist', wordlist_id=6666666, _external=True)
            r = self.client.get(url)
            self.assertEqual(404, r.status_code)

    # tests for changing list type; many cases

    # change list type: create empty, change to standard
    def test_change_list_type_empty_to_standard(self):
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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
        with self.app.test_request_context():
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

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
            obj = json.loads(r.data)
            self.wordlist_id = obj['wordlist_id']

            # create a word
            word = ''.join(random.choices(string.ascii_lowercase, k=10))
            add_payload = {
                "word": word,
                "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            }
            r = self.client.post(url_for('api_word.add_word', _external=True), json=add_payload)
            obj = json.loads(r.data)
            self.word_id = obj['word_id']

            self.metadata_update_url = url_for('api_wordlist.update_wordlist_metadata',
                                               wordlist_id=self.wordlist_id,
                                               _external=True)

    def tearDown(self):
        with self.app.test_request_context():
            self.client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=self.wordlist_id,
                                       _external=True))
            with self.app.test_request_context():
                self.client.delete(url_for('api_word.delete_word', word_id=self.word_id, _external=True))

    # do nothing, just make sure that setUp and tearDown work
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


