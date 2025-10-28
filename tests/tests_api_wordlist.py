import unittest
import requests
from dlernen import config
import json
import random
import string

# TODO - test updating a list's name to null, empty string, or other bullshit values.
#   also test creating a list with a bullshit name.


class APIWordlist(unittest.TestCase):
    # add list with no words, just a name
    def test_create_empty_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        # do a GET - known and unknown lists should be empty
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual("empty", obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

        # do a GET - should be gone
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 404)

        # getting the list metadata should also be well-behaved
        r = requests.get("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 404)

    # add list with everything, incl. known and unknown words
    def test_create_dumb_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'words': [
                'werfen',  # known
                'natehdnaoehu'  # unknown, hopefully
            ],
            'notes': 'important notes',
            'citation': 'confidential'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # add smart list with everything
    def test_create_smart_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'notes': 'important notes',
            'source': 'confidential',
            'sqlcode': 'select id word_id from word where id = 124'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual("smart", obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # update list
    def test_update_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'name': list_name + "__RENAMED",
            'notes': 'notes here',
            'sqlcode': 'select id word_id from word where id = 100',
            'citation': 'some article'
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        for k in update_payload.keys():
            self.assertEqual(update_payload[k], obj[k])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # add word to list
    def test_add_words_to_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        gibberish = 'aoeunhatedu'
        add_payload = {
            'name': list_name,
            'words': [
                'werfen',
                'geben',
                gibberish
            ]
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'words': [
                'wecken',
                'werfen',  # already there, should be a noop
                'nachgebend',
                gibberish
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        known_words = {x['word'] for x in obj['known_words']}
        unknown_words = {x for x in obj['unknown_words']}

        self.assertEqual({'wecken', 'nachgebend', 'geben', 'werfen'}, known_words)
        self.assertEqual({gibberish}, unknown_words)

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # update list with empty payload --> noop
    def test_update_list_empty_payload(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': """select id word_id from word where word = 'geben'"""
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        wordlist_id = obj['wordlist_id']

        update_payload = {
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, wordlist_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        for k in add_payload.keys():
            self.assertEqual(add_payload[k], obj[k])

        self.assertTrue(len(obj['known_words']) > 0)

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 200)

    # remove word by word from list -> removes from unknown
    def test_remove_word_by_word(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            'name': list_name,
            'words': [
                'werfen',  # known
                gibberish  # unknown, hopefully
            ],
            'notes': 'important notes',
            'citation': 'confidential'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertTrue(len(obj['unknown_words']) > 0)
        word = obj['unknown_words'][0]
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, list_id, word))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # remove word by id from list
    def test_remove_word_by_id(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'words': [
                'werfen',  # known
                'natehdnaoehu'  # unknown, hopefully
            ],
            'notes': 'important notes',
            'citation': 'confidential'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertTrue(len(obj['known_words']) > 0)
        word_id = obj['known_words'][0]['word_id']
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, list_id, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(0, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    def test_update_smart_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'notes': 'important notes',
            'citation': 'confidential',
            'sqlcode': 'select id word_id from word where id = 124'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        new_code = 'select id word_id from word where id = 666'
        new_name = "%s%s" % (list_name, '__UPDATED')
        new_citation = 'really confidential'
        payload = {
            'name': new_name,
            'citation': new_citation,
            'sqlcode': new_code
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        r = requests.get("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, list_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(new_code, obj['sqlcode'])
        self.assertEqual(new_citation, obj['citation'])
        self.assertEqual(new_name, obj['name'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # add list with existing name
    def test_add_existing_name(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 500)

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # add list with empty name
    def test_add_empty_name(self):
        list_name = " "
        payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 400)

    # add list with empty payload
    def test_add_empty_payload(self):
        payload = {
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 400)

    # update list with empty name
    def test_update_with_empty_name(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))

        # don't allow create or update with empty name

        # create a word list

        create_url = "%s/api/wordlist" % config.Config.DB_URL
        payload = {
            'name': ''
        }
        r = requests.post(create_url, json=payload)
        self.assertEqual(400, r.status_code)

        payload = {
            'name': list_name
        }
        r = requests.post(create_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        # set list name to empty string - should be error

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        payload = {
            'name': ''
        }
        r = requests.put(url, json=payload)
        self.assertNotEqual(r.status_code, 200)

        # make sure the list name wasn't changed

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        self.assertEqual(list_name, result['name'])

        # clean up

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)

    # update list with notes as empty string
    def test_update_notes_to_empty_string(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))

        create_url = "%s/api/wordlist" % config.Config.DB_URL
        payload = {
            'name': list_name,
            'notes': 'aosthedunthaoe'
        }
        r = requests.post(create_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        # set notes to empty string - should succeed

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        payload = {
            'notes': ''
        }
        r = requests.put(url, json=payload)
        self.assertEqual(r.status_code, 200)

        # make sure the notes were cleared

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        self.assertEqual('', result['notes'])

        # clean up

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)

    # update list with notes as None
    def test_update_notes_to_None(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))

        create_url = "%s/api/wordlist" % config.Config.DB_URL
        payload = {
            'name': list_name,
            'notes': 'aosthedunthaoe'
        }
        r = requests.post(create_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        # set notes to empty string - should succeed

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        payload = {
            'notes': None
        }
        r = requests.put(url, json=payload)
        self.assertEqual(r.status_code, 200)

        # make sure the notes were cleared

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        self.assertIsNone(result['notes'])

        # clean up

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)

    # update something other than the notes and make sure the notes didn't get bashed
    def test_update_does_not_affect_notes(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))

        create_url = "%s/api/wordlist" % config.Config.DB_URL
        notes = 'anhtoednaoehduntaeo'
        payload = {
            'name': list_name,
            'notes': notes
        }
        r = requests.post(create_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        # update the name then check the notes

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        payload = {
            'name': list_name + list_name
        }
        r = requests.put(url, json=payload)
        self.assertEqual(r.status_code, 200)

        # make sure the notes were unaffected

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        self.assertEqual(notes, result['notes'])

        # clean up

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)

    # add list with code and words --> only one is allowed.
    def test_add_list_with_code_and_words(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 666',
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 400)

    # add code to dumb list --> not allowed if list has words, ok if empty
    def test_add_code_to_dumb_list(self):
        # not allowed
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(400, r.status_code)

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)

    # add words to smart list --> not allowed.
    def test_add_words_to_smart_list(self):
        # not allowed
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(400, r.status_code)

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # get with bullshit wordlist id
    def test_get_bullshit_wordlist_id(self):
        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, 6666666)
        r = requests.get(url)
        self.assertEqual(404, r.status_code)

    # tests for changing list type; many cases

    # change list type: create empty, change to standard
    def test_change_list_type_empty_to_standard(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('empty', obj['list_type'])

        update_payload = {
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('standard', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # change list type: create empty, change to smart
    def test_change_list_type_empty_to_smart(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('empty', obj['list_type'])

        update_payload = {
            'sqlcode': 'select id word_id from word where id = 111'
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('smart', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # change list type: create smart, change to empty
    def test_change_list_type_smart_to_empty(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('smart', obj['list_type'])

        update_payload = {
            'sqlcode': None
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('empty', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # change list type: create smart, change to standard
    def test_change_list_type_smart_to_standard(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('smart', obj['list_type'])

        update_payload = {
            'sqlcode': None,
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('standard', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # there is no test for create standard, change to smart
    # because this can't be done in one request.  we have to empty the list first
    # then change to smart.

    # change list type: create standard, change to empty
    def test_change_list_type_standard_to_empty(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            'name': list_name,
            'words': [
                'werfen',
                gibberish
            ]
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('standard', obj['list_type'])
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual(1, len(obj['known_words']))

        # remove the words one by one
        word = obj['unknown_words'][0]
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, list_id, word))
        self.assertEqual(r.status_code, 200)

        word_id = obj['known_words'][0]['word_id']
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, list_id, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        obj = r.json()

        self.assertEqual('empty', obj['list_type'])
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual(0, len(obj['known_words']))

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # removing words from a smart list should not be possible.  let's verify that.
    def test_remove_words_from_smart_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('smart', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s/666" % (config.Config.BASE_URL, list_id))
        self.assertNotEqual(200, r.status_code)

        r = requests.delete("%s/api/wordlist/%s/teuhdunaoethu" % (config.Config.BASE_URL, list_id))
        self.assertNotEqual(200, r.status_code)

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)
