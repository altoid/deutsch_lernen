import unittest
import requests
from dlernen import config
from pprint import pprint
import random
import string


class APITestsWordEndToEnd(unittest.TestCase):
    # end-to-end test:  add a word, verify existence, delete it, verify deletion.
    # delete it again, should be no errors.

    def test_basic_add(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_name": "noun",
            "attributes_adding": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id = obj['word_id']

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        self.assertTrue('word_id' in obj)

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(404, r.status_code)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(404, r.status_code)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word))
        self.assertEqual(404, r.status_code)

        # delete it again, should not cause error
        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

    # add a word with empty attributes list
    def test_add_empty_attributes_list(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_name": "noun",
            "attributes_adding": [
            ]
        }
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id = obj['word_id']

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        self.assertTrue('word_id' in obj)

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

    # add a word with no attributes list
    def test_add_without_attributes(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_name": "noun"
        }
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id = obj['word_id']

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        self.assertTrue('word_id' in obj)

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

    # another end-to-end test, but without giving any attributes.  add attributes to the word.  retrieve
    # word, new attributes should be there.
    def test_add_attrs(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_name": "noun",
        }
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id = obj['word_id']

        update_payload = {
            "attributes_adding": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        attrdict = {r['attrkey']: r['attrvalue'] for r in obj['attributes']}
        attrkeys = set(attrdict.keys())

        self.assertEqual({'article', 'plural', 'definition'}, attrkeys)
        self.assertEqual("der", attrdict['article'])
        self.assertEqual("Xxxxxxxxxx", attrdict['plural'])
        self.assertEqual("feelthy", attrdict['definition'])

        # update again but with empty attribute lists

        update_payload = {
            "attributes_adding": [
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(3, len(obj['attributes']))

        attrdict = {r['attrkey']: r['attrvalue'] for r in obj['attributes']}
        attrkeys = set(attrdict.keys())

        self.assertEqual({'article', 'plural', 'definition'}, attrkeys)
        self.assertEqual("der", attrdict['article'])
        self.assertEqual("Xxxxxxxxxx", attrdict['plural'])
        self.assertEqual("feelthy", attrdict['definition'])

        # update AGAIN but with empty payload.

        update_payload = {
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(3, len(obj['attributes']))

        attrdict = {r['attrkey']: r['attrvalue'] for r in obj['attributes']}
        attrkeys = set(attrdict.keys())

        self.assertEqual({'article', 'plural', 'definition'}, attrkeys)
        self.assertEqual("der", attrdict['article'])
        self.assertEqual("Xxxxxxxxxx", attrdict['plural'])
        self.assertEqual("feelthy", attrdict['definition'])

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

    # adding the same word twice is not allowed if the part of speech is the same.
    def test_add_twice_same_pos(self):
        word = "test_add_twice_%s" % ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            "word": word,
            "pos_name": "noun",
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id_1 = obj['word_id']

        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=payload)
        self.assertNotEqual(r.status_code, 200)

        # get word by name
        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word))
        obj = r.json()
        self.assertEqual(1, len(obj))

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_1))
        self.assertEqual(r.status_code, 200)

    # adding the same word twice is ok, as long as they are different parts of speech.  should have different word ids.
    def test_add_twice_different_pos(self):
        word = "test_add_twice_%s" % ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            "word": word,
            "pos_name": "noun",
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id_1 = obj['word_id']

        payload = {
            "word": word,
            "pos_name": "adjective",
            "attributes": [
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }

        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)

        obj = r.json()
        word_id_2 = obj['word_id']

        self.assertNotEqual(word_id_1, word_id_2)

        # get word by name
        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word))
        obj = r.json()
        self.assertEqual(2, len(obj))

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_1))
        self.assertEqual(r.status_code, 200)

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_2))
        self.assertEqual(r.status_code, 200)


class APITestsWordPOST(unittest.TestCase):
    # this class tests error conditions.  tests that the api works correctly with correct input are
    # in APITestsWordEndToEnd

    # word not in payload
    def test_word_not_in_payload(self):
        payload = {
            "pos_name": "noun",
            "attributes_adding": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
        self.assertNotEqual(r.status_code, 200)

    # pos not in payload
    def test_pos_not_in_payload(self):
        payload = {
            "word": "aonsetuhasoentuh",
            "attributes_adding": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
        self.assertNotEqual(r.status_code, 200)

    # payload not json
    def test_payload_not_json(self):
        payload = "this is some bullshit right here"
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
        self.assertNotEqual(r.status_code, 200)

    # attr keys are bullshit
    def test_bullshit_attrkeys(self):
        payload = {
            "word": "aoeiaoueaou",
            "pos_name": "noun",
            "attributes_adding": [
                {
                    "attrkey": "stinky",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "foofoo",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "legal attrkey here"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
        self.assertNotEqual(r.status_code, 200)

    # part of speech is bullshit
    def test_bullshit_pos(self):
        payload = {
            "word": "aeioeauaoeu",
            "pos_name": "uiauiauoeu",
            "attributes_adding": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
        self.assertNotEqual(r.status_code, 200)


class APITestsWordPUT(unittest.TestCase):
    def setUp(self):
        self.word = "APITestsWordPut_" + ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": self.word,
            "pos_name": "noun"
        }

        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.obj = r.json()
        self.word_id = self.obj['word_id']

    def tearDown(self):
        requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))

    # bullshit word id
    def test_bullshit_word_id(self):
        update_payload = {
            "word": "blah",
            "attributes_updating": [
                {
                    "attrvalue_id": self.obj['attributes'][0]['attrvalue_id'],
                    "attrvalue": "der"
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, 5555555555), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # bullshit attr ids
    def test_update_bullshit_attrids(self):
        update_payload = {
            "word": "blah",
            "attributes_updating": [
                {
                    "attrvalue_id": 5555555555555,
                    "attrvalue": "der"
                },
                {
                    "attrvalue_id": 666666666666666,
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    def test_delete_bullshit_attrids(self):
        update_payload = {
            "word": "blah",
            "attributes_deleting": [
                555555555555555,
                666666666666666
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # zero-length word
    def test_zero_length_word(self):
        # updating with word = "" not allowed.
        update_payload = {
            "word": "",
            "attributes_updating": [
                {
                    "attrvalue_id": self.obj['attributes'][0]['attrvalue_id'],
                    "attrvalue": "der"
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # zero-length attrkey value
    def test_zero_length_attrvalue(self):
        # updating with attrvalue = "" not allowed.
        update_payload = {
            "word": "aoeuoae",
            "attributes_updating": [
                {
                    "attrvalue_id": self.obj['attributes'][0]['attrvalue_id'],
                    "attrvalue": ""
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # attrvalue keyword missing
    def test_attrvalue_keyword_missing(self):
        update_payload = {
            "word": "aoeuoae",
            "attributes_updating": [
                {
                    "attrvalue_id": self.obj['attributes'][0]['attrvalue_id']
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # attrvalue_id keyword missing
    def test_attrvalue_id_keyword_missing(self):
        update_payload = {
            "word": "aoeuoae",
            "attributes_updating": [
                {
                    "attrvalue": "turnips"
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # payload not json
    def test_payload_not_json(self):
        update_payload = "serious bullshit right here"

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # changing the spelling of a word works.
    def test_change_spelling(self):
        new_word = 'aoeuaeouoeau'
        update_payload = {
            'word': new_word
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        obj = r.json()
        self.assertEqual(new_word, obj['word'])

    # updating attrkey values works.
    def test_update_attrs(self):
        # since we created the word with no attributes, add one that we can update.

        attrkey = "definition"
        payload = {
            'attributes_adding': [
                {
                    "attrvalue": "male bovine excrement",
                    "attrkey": attrkey
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        attr_changed = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        victim = attr_changed[0]['attrvalue_id']
        new_value = 'changed to this'
        payload = {
            'attributes_updating': [
                {
                    'attrvalue_id': victim,
                    'attrvalue': new_value
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        a = list(filter(lambda x: x['attrvalue_id'] == victim, obj['attributes']))
        self.assertEqual(1, len(a))
        self.assertEqual(new_value, a[0]['attrvalue'])

    # trivial no-op payload is ok.
    def test_noop_update(self):
        update_payload = {
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        obj = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(3, len(obj['attributes']))
        self.assertEqual(self.word, obj['word'])


class APIWordUpdate(unittest.TestCase):
    def setUp(self):
        # create a random verb
        self.verb = ''.join(random.choices(string.ascii_lowercase, k=11))
        add_payload = {
            "word": self.verb,
            "pos_name": "verb"
        }

        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        obj = r.json()
        self.word_id = obj['word_id']

    def tearDown(self):
        requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))

    def test_add_update_delete_attribute_1(self):
        # add, update, and delete the same attr value in 3 separate requests
        old_def = "it smells like cereal here"
        attrkey = "definition"
        payload = {
            "attributes_adding": [
                {
                    "attrkey": attrkey,
                    "attrvalue": old_def
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertEqual(old_def, defn['attrvalue'])

        # update definition
        new_def = "try this on for size"

        payload = {
            "attributes_updating": [
                {
                    "attrvalue_id": defn['attrvalue_id'],
                    "attrvalue": new_def
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertEqual(new_def, defn['attrvalue'])

        # delete
        payload = {
            "attributes_deleting": [
                defn['attrvalue_id']
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertIsNone(defn['attrvalue'])

    def test_add_update_delete_attribute_2(self):
        # add, update, and delete attrkey values in a single request
        old_def = "it smells like cereal here"
        payload = {
            "attributes_adding": [
                {
                    "attrkey": "definition",
                    "attrvalue": old_def
                },
                {
                    "attrkey": "first_person_singular",
                    "attrvalue": "mr_lonely"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        # remove the definition, add 2nd person singular, update 1st person singular, in one request
        fps = list(filter(lambda x: x['attrkey'] == 'first_person_singular', obj['attributes']))[0]
        defn = list(filter(lambda x: x['attrkey'] == 'definition', obj['attributes']))[0]

        new_fps = "what hath god wrought"
        sps_val = "my nose hurts"
        payload = {
            "attributes_adding": [
                {
                    "attrkey": "second_person_singular",
                    "attrvalue": sps_val
                }
            ],
            "attributes_deleting": [
                defn['attrvalue_id']
            ],
            "attributes_updating": [
                {
                    "attrvalue_id": fps['attrvalue_id'],
                    "attrvalue": new_fps
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        fps = list(filter(lambda x: x['attrkey'] == 'first_person_singular', obj['attributes']))[0]
        sps = list(filter(lambda x: x['attrkey'] == 'second_person_singular', obj['attributes']))[0]
        defn = list(filter(lambda x: x['attrkey'] == 'definition', obj['attributes']))[0]

        self.assertEqual(new_fps, fps['attrvalue'])
        self.assertEqual(sps_val, sps['attrvalue'])
        self.assertIsNone(defn['attrvalue'])

    def test_update_delete_same_attr(self):
        # error if we attempt to update and delete the same attr id.
        old_def = "it smells like cereal here"
        attrkey = "definition"
        payload = {
            "attributes_adding": [
                {
                    "attrkey": attrkey,
                    "attrvalue": old_def
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        defn = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))[0]

        payload = {
            "attributes_updating": [
                {
                    "attrvalue_id": defn['attrvalue_id'],
                    "attrvalue": "not the same at all"
                }
            ],
            "attributes_deleting": [
                defn['attrvalue_id']
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertNotEqual(200, r.status_code)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        self.assertEqual(200, r.status_code)
        obj = r.json()
        defn = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))[0]
        self.assertEqual(old_def, defn['attrvalue'])



