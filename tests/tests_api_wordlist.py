import unittest
import requests
from dlernen import config
import json
import random
import string


class APIWordlist(unittest.TestCase):
    def setUp(self):
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=add_payload)
        obj = r.json()
        self.wordlist_id = obj['wordlist_id']
        self.contents_url = "%s/api/wordlist/%s/contents" % (config.Config.BASE_URL, self.wordlist_id)
        self.metadata_url = "%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id)
        self.wordlist_url = "%s/api/wordlist/%s" % (config.Config.BASE_URL, self.wordlist_id)

    def tearDown(self):
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, self.wordlist_id))

    # the setup for this class creates a list with just a name.

    # add list with everything, incl. known and unknown words
    def test_create_dumb_list(self):
        payload = {
            'words': [
                'werfen',  # known
                'natehdnaoehu'  # unknown, hopefully
            ],
            'notes': 'important notes'
        }

        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, self.wordlist_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

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

        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(r.status_code, 200)

        payload = {
            'words': [
                'wecken',
                'werfen',  # already there, should be a noop
                'nachgebend',
                gibberish
            ]
        }

        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

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

        r = requests.put(self.metadata_url, json=metadata_payload)
        self.assertEqual(r.status_code, 200)

        update_payload = {
        }

        r = requests.put(self.contents_url, json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, self.wordlist_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

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

        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertTrue(len(obj['unknown_words']) > 0)
        word = obj['unknown_words'][0]
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, self.wordlist_id, word))
        self.assertEqual(r.status_code, 200)

        r = requests.get(self.wordlist_url)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

    # remove word by id from list
    def test_remove_word_by_id(self):
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            'words': [
                'werfen',  # known
                gibberish  # unknown, hopefully
            ]
        }

        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertTrue(len(obj['known_words']) > 0)
        word_id = obj['known_words'][0]['word_id']
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, self.wordlist_id, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get(self.wordlist_url)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(0, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

    # update list with notes as empty string
    def test_update_notes_to_empty_string(self):
        payload = {
            'notes': ''
        }
        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(r.status_code, 200)

        # make sure the notes were cleared

        r = requests.get(self.wordlist_url)
        obj = r.json()
        self.assertEqual('', obj['notes'])

    # update list with notes as None
    def test_update_notes_to_None(self):
        notes = 'euioeuiaoeuaoeu'
        payload = {
            'notes': notes
        }
        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(200, r.status_code)

        r = requests.get(self.wordlist_url)
        obj = r.json()
        self.assertEqual(notes, obj['notes'])

        # set notes to None - should succeed

        payload = {
            'notes': None
        }
        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(r.status_code, 200)

        # make sure the notes were cleared

        r = requests.get(self.wordlist_url)
        obj = r.json()
        self.assertIsNone(obj['notes'])

    # update something other than the notes and make sure the notes didn't get bashed
    def test_update_does_not_affect_notes(self):
        notes = 'anhtoednaoehduntaeo'
        payload = {
            'notes': notes
        }
        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(200, r.status_code)

        # add some words then check the notes

        payload = {
            'words': [
                'one',
                'two',
                'aoeuao'
            ]
        }
        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(r.status_code, 200)

        # make sure the notes were unaffected

        r = requests.get(self.wordlist_url)
        result = r.json()
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

        r = requests.put(self.contents_url, json=add_payload)
        self.assertEqual(200, r.status_code)

        update_payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.put(self.metadata_url, json=update_payload)
        self.assertEqual(400, r.status_code)

    # add words to smart list --> not allowed.
    def test_add_words_to_smart_list(self):
        # not allowed
        payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.put(self.metadata_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('smart', obj['list_type'])

        payload = {
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(400, r.status_code)

    # get with bullshit wordlist id
    def test_get_bullshit_wordlist_id(self):
        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, 6666666)
        r = requests.get(url)
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

        r = requests.put("%s/api/wordlist/%s/contents" % (config.Config.BASE_URL, self.wordlist_id),
                         json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('standard', obj['list_type'])

    # change list type: create smart, change to empty
    def test_change_list_type_smart_to_empty(self):
        payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('smart', obj['list_type'])

        payload = {
            'sqlcode': None
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
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

        r = requests.put(self.contents_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        self.assertEqual('standard', obj['list_type'])
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual(1, len(obj['known_words']))

        # remove the words one by one
        word = obj['unknown_words'][0]
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, self.wordlist_id, word))
        self.assertEqual(r.status_code, 200)

        word_id = obj['known_words'][0]['word_id']
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, self.wordlist_id, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get(self.wordlist_url)
        obj = r.json()

        self.assertEqual('empty', obj['list_type'])
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual(0, len(obj['known_words']))

    # removing words from a smart list should not be possible.  let's verify that.
    def test_remove_words_from_smart_list(self):
        payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        self.assertEqual('smart', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s/666" % (config.Config.BASE_URL, self.wordlist_id))
        self.assertNotEqual(200, r.status_code)

        r = requests.delete("%s/api/wordlist/%s/teuhdunaoethu" % (config.Config.BASE_URL, self.wordlist_id))
        self.assertNotEqual(200, r.status_code)
