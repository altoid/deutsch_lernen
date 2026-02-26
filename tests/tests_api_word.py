import unittest
import json
from dlernen import create_app, dlernen_json_schema as js
from flask import url_for
from pprint import pprint
import random
import string


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id))


class APITestsWordNotes(unittest.TestCase):
    # tests for operations on word notes.

    app = None
    app_context = None
    keyword_mappings = None
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

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # create a word with no notes.  fetch the word and verify notes are None.
    def test1(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            "notes": None,
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertIsNone(obj['notes'])

    # create a word with no notes.  add notes via update.  verify.
    def test2(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            "notes": None,
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)
        self.assertIsNone(obj['notes'])

        new_notes = "rubba dubba"

        payload = {
            "notes": new_notes
        }

        r = self.client.put(url_for('api_word.update_word', word_id=word_id), json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertEqual(new_notes, obj['notes'])

    # create a word with notes.  fetch the word and verify the notes.
    def test3(self):
        notes = "do re mi"
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            "notes": notes,
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertEqual(notes, obj['notes'])

    # create a word with notes.  change the notes via update.  verify.
    def test4(self):
        old_notes = "do re mi"
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            "notes": old_notes,
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)
        self.assertEqual(old_notes, obj['notes'])

        new_notes = "rubba dubba"

        payload = {
            "notes": new_notes
        }

        r = self.client.put(url_for('api_word.update_word', word_id=word_id), json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertEqual(new_notes, obj['notes'])

    # create a word with notes.  remove the notes via update.  verify notes are None.
    def test5(self):
        old_notes = "do re mi"
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            "notes": old_notes,
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)
        self.assertEqual(old_notes, obj['notes'])

        payload = {
            "notes": None
        }

        r = self.client.put(url_for('api_word.update_word', word_id=word_id), json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertIsNone(obj['notes'])

    # create a word with notes that are all whitespace, then fetch.  value of notes should be None.
    def test6(self):
        old_notes = "   "
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            "notes": old_notes,
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)
        self.assertIsNone(obj['notes'])

    # create a word; update its notes to all whitespace, then retrieve.  value of notes should be None.
    def test7(self):
        old_notes = "do re mi"
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            "notes": old_notes,
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)
        self.assertEqual(old_notes, obj['notes'])

        new_notes = "   "

        payload = {
            "notes": new_notes
        }

        r = self.client.put(url_for('api_word.update_word', word_id=word_id), json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertIsNone(obj['notes'])


class APITestsWordEndToEnd(unittest.TestCase):
    app = None
    app_context = None
    keyword_mappings = None
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

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # insert a word with 'ss' but look it up with 'ß'.  should succeed.
    def test_add_ss_lookup_with_eszet(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word + 'ss',
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        r = self.client.get(url_for('api_word.get_word', word=word + 'ß'))
        self.assertEqual(200, r.status_code)

    # insert a word with 'ß' but look it up with 'ss'.  should succeed.
    def test_add_eszet_lookup_with_ss(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word + 'ß',
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        r = self.client.get(url_for('api_word.get_word', word=word + 'ss'))
        self.assertEqual(200, r.status_code)

    # end-to-end test:  add a word, verify existence, delete it, verify deletion.
    # delete it again, should be no errors.
    def test_basic_add(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['plural'],
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertTrue('word_id' in obj)

        r = self.client.delete(url_for('api_word.delete_word', word_id=word_id))
        self.assertEqual(r.status_code, 200)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(404, r.status_code)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(404, r.status_code)

        r = self.client.get(url_for('api_word.get_word', word=word))
        self.assertEqual(404, r.status_code)

        # delete it again, should not cause error
        r = self.client.delete(url_for('api_word.delete_word', word_id=word_id))
        self.assertEqual(r.status_code, 200)

    # enforce capitalization of nouns
    def test_noun_capitalization(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        word_capitalized = word.capitalize()

        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun']
        }

        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        self.assertEqual(word_capitalized, obj['word'])

        r = self.client.delete(url_for('api_word.delete_word', word_id=obj['word_id']))
        self.assertEqual(r.status_code, 200)

    # enforce capitalization of noun plurals on add
    def test_noun_plurals_adding(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        word_capitalized = word.capitalize()
        attrkey = 'plural'
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids'][attrkey],
                    "attrvalue": word
                },
            ]
        }

        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        self.addCleanup(cleanupWordID, self.client, obj['word_id'])

        plural = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))[0]
        self.assertEqual(word_capitalized, plural['attrvalue'])

        r = self.client.delete(url_for('api_word.delete_word', word_id=obj['word_id']))
        self.assertEqual(r.status_code, 200)

    # enforce capitalization of noun plurals on update
    def test_noun_plurals_updating(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        word_capitalized = word.capitalize()
        attrkey = 'plural'
        attribute_id = self.keyword_mappings['attribute_names_to_ids']['plural']
        payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            js.ATTRIBUTES: [
                {
                    "attribute_id": attribute_id,
                    "attrvalue": word
                },
            ]
        }

        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        self.addCleanup(cleanupWordID, self.client, obj['word_id'])

        plural_attr = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))[0]
        self.assertEqual(word_capitalized, plural_attr['attrvalue'])

        new_word = ''.join(random.choices(string.ascii_lowercase, k=10))
        new_word_capitalized = new_word.capitalize()

        payload = {
            js.ATTRIBUTES: [
                {
                    "attrvalue": new_word,
                    "attribute_id": attribute_id,
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=obj['word_id']), json=payload)
        self.assertEqual(r.status_code, 200)

        obj = json.loads(r.data)
        plural = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))[0]
        self.assertEqual(new_word_capitalized, plural['attrvalue'])

        r = self.client.delete(url_for('api_word.delete_word', word_id=obj['word_id']))
        self.assertEqual(r.status_code, 200)

    # add a word with empty attributes list
    def test_add_empty_attributes_list(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            js.ATTRIBUTES: [
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertTrue('word_id' in obj)

        r = self.client.delete(url_for('api_word.delete_word', word_id=word_id))
        self.assertEqual(r.status_code, 200)

    # add a word with no attributes list
    def test_add_without_attributes(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)
        self.assertTrue('word_id' in obj)

        r = self.client.delete(url_for('api_word.delete_word', word_id=word_id))
        self.assertEqual(r.status_code, 200)

    # another end-to-end test, but without giving any attributes.  add attributes to the word.  retrieve
    # word, new attributes should be there.
    def test_add_attrs(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        self.addCleanup(cleanupWordID, self.client, obj['word_id'])

        update_payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['plural'],
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=obj['word_id']),
                            json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        attrdict = {r['attrkey']: r['attrvalue'] for r in obj['attributes']}
        attrkeys = set(attrdict.keys())

        self.assertEqual({'article', 'plural', 'definition'}, attrkeys)
        self.assertEqual("der", attrdict['article'])
        self.assertEqual("Xxxxxxxxxx", attrdict['plural'])
        self.assertEqual("feelthy", attrdict['definition'])

        # update again but with empty attribute lists

        update_payload = {
            js.ATTRIBUTES: [
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=obj['word_id']),
                            json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

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

        r = self.client.put(url_for('api_word.update_word', word_id=obj['word_id']),
                            json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(3, len(obj['attributes']))

        attrdict = {r['attrkey']: r['attrvalue'] for r in obj['attributes']}
        attrkeys = set(attrdict.keys())

        self.assertEqual({'article', 'plural', 'definition'}, attrkeys)
        self.assertEqual("der", attrdict['article'])
        self.assertEqual("Xxxxxxxxxx", attrdict['plural'])
        self.assertEqual("feelthy", attrdict['definition'])

        r = self.client.delete(url_for('api_word.delete_word', word_id=obj['word_id']))
        self.assertEqual(r.status_code, 200)

    # adding the same word twice is not allowed if the part of speech is the same.
    def test_add_twice_same_pos(self):
        word = "test_add_twice_%s" % ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['plural'],
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        self.addCleanup(cleanupWordID, self.client, obj['word_id'])
        word_id_1 = obj['word_id']

        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertNotEqual(r.status_code, 201)

        # get word by name
        r = self.client.get(url_for('api_word.get_word', word=word))
        obj = json.loads(r.data)
        self.assertEqual(1, len(obj))

        r = self.client.delete(url_for('api_word.delete_word', word_id=word_id_1))
        self.assertEqual(r.status_code, 200)

    # adding the same word twice is ok, as long as they are different parts of speech.  should have different word ids.
    def test_add_twice_different_pos(self):
        word = "test_add_twice_%s" % ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['plural'],
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        self.addCleanup(cleanupWordID, self.client, obj['word_id'])
        word_id_1 = obj['word_id']

        payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }

        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(r.status_code, 201)

        obj = json.loads(r.data)
        self.addCleanup(cleanupWordID, self.client, obj['word_id'])
        word_id_2 = obj['word_id']

        self.assertNotEqual(word_id_1, word_id_2)

        # get word by name
        r = self.client.get(url_for('api_word.get_word', word=word))
        obj = json.loads(r.data)
        self.assertEqual(2, len(obj))

        r = self.client.delete(url_for('api_word.delete_word', word_id=word_id_1))
        self.assertEqual(r.status_code, 200)

        r = self.client.delete(url_for('api_word.delete_word', word_id=word_id_2))
        self.assertEqual(r.status_code, 200)


class APITestsWordPOST(unittest.TestCase):
    # this class tests error conditions.  tests that the api works correctly with correct input are
    # in APITestsWordEndToEnd

    client = None
    app = None
    app_context = None
    keyword_mappings = None

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

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # word not in payload
    def test_word_not_in_payload(self):
        payload = {
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['plural'],
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertNotEqual(r.status_code, 201)

    # pos not in payload
    def test_pos_not_in_payload(self):
        payload = {
            "word": "aonsetuhasoentuh",
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['plural'],
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertNotEqual(r.status_code, 201)

    # payload not json
    def test_payload_not_json(self):
        payload = "this is some bullshit right here"
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertNotEqual(r.status_code, 201)

    # attr ids are bullshit
    def test_bullshit_attribute_ids(self):
        payload = {
            "word": "aoeiaoueaou",
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun'],
            js.ATTRIBUTES: [
                {
                    "attribute_id": 5346345,
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "legal attribute_id here"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertNotEqual(r.status_code, 201)

    # part of speech is bullshit
    def test_bullshit_pos(self):
        payload = {
            "word": "aeioeauaoeu",
            "pos_id": 92378456,
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['plural'],
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertNotEqual(r.status_code, 201)


class APITestsWordPUT(unittest.TestCase):
    app = None
    app_context = None
    client = None
    keyword_mappings = None

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

    def setUp(self):
        self.word = "Apitestswordput_" + ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": self.word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['noun']
        }

        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.obj = json.loads(r.data)
        self.word_id = self.obj['word_id']
        self.addCleanup(cleanupWordID, self.client, self.word_id)

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # bullshit word id
    def test_bullshit_word_id(self):
        update_payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=555555555), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # bullshit attr ids
    def test_update_bullshit_attrids(self):
        update_payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": 5555555555555,
                    "attrvalue": "der"
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    def test_delete_bullshit_attrids(self):
        update_payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": 4345345345
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # zero-length word
    def test_zero_length_word(self):
        # updating with word = "" not allowed.
        update_payload = {
            "word": "",
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['article'],
                    "attrvalue": "der"
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # zero-length attribute value
    def test_zero_length_attrvalue(self):
        # updating with attrvalue = "" not allowed.
        update_payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": ""
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # attribute_id keyword missing
    def test_attrvalue_keyword_missing(self):
        update_payload = {
            js.ATTRIBUTES: [
                {
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # payload not json
    def test_payload_not_json(self):
        update_payload = "serious bullshit right here"

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # changing the spelling of a word works.
    def test_change_spelling(self):
        new_word = 'Aoeuaeouoeau'
        update_payload = {
            'word': new_word
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=self.word_id))
        obj = json.loads(r.data)
        self.assertEqual(new_word, obj['word'])

    # updating attribute values works.
    def test_update_attrs(self):
        # since we created the word with no attributes, add one that we can update.

        attrkey = 'definition'
        attribute_id = self.keyword_mappings['attribute_names_to_ids'][attrkey]
        payload = {
            js.ATTRIBUTES: [
                {
                    "attrvalue": "male bovine excrement",
                    "attribute_id": attribute_id
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(r.status_code, 200)

        new_value = 'changed to this'
        payload = {
            js.ATTRIBUTES: [
                {
                    'attribute_id': attribute_id,
                    'attrvalue': new_value
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(r.status_code, 200)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=self.word_id))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        a = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        self.assertEqual(1, len(a))
        self.assertEqual(new_value, a[0]['attrvalue'])

    # trivial no-op payload is ok.
    def test_noop_update(self):
        update_payload = {
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=self.word_id))
        obj = json.loads(r.data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(3, len(obj['attributes']))
        self.assertEqual(self.word, obj['word'])


class APIWordUpdate(unittest.TestCase):
    app = None
    app_context = None
    client = None
    keyword_mappings = None

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

    def setUp(self):
        # create a random verb
        self.verb = ''.join(random.choices(string.ascii_lowercase, k=11))
        add_payload = {
            "word": self.verb,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['verb'],
        }

        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        obj = json.loads(r.data)
        self.word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, self.word_id)

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # this bit me in the aß.  a spell change of 'schoss' to 'schoß' was seen as no change and was not being updated
    # in the word table.
    def test_double_s_to_estzet(self):
        new_word = self.verb + "ss"

        payload = {
            "word": new_word
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(new_word, obj['word'])
        first_change = new_word

        new_word = self.verb + "ß"

        payload = {
            "word": new_word
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(new_word, obj['word'])
        self.assertNotEqual(first_change, obj['word'])

    def test_estzet_to_double_s(self):
        new_word = self.verb + "ß"

        payload = {
            "word": new_word
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(new_word, obj['word'])
        first_change = new_word

        new_word = self.verb + "ss"

        payload = {
            "word": new_word
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertEqual(new_word, obj['word'])
        self.assertNotEqual(first_change, obj['word'])

    def test_add_update_delete_attribute_1(self):
        # add, update, and delete the same attr value in 3 separate requests
        old_def = "it smells like cereal here"
        attrkey = 'definition'
        attribute_id = self.keyword_mappings['attribute_names_to_ids'][attrkey]
        payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": attribute_id,
                    "attrvalue": old_def
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertEqual(old_def, defn['attrvalue'])

        # update definition
        new_def = "try this on for size"

        payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": attribute_id,
                    "attrvalue": new_def
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertEqual(new_def, defn['attrvalue'])

        # delete
        payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": attribute_id
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertIsNone(defn['attrvalue'])

    def test_add_update_delete_attribute_2(self):
        # add, update, and delete attribute values in a single request
        old_def = "it smells like cereal here"
        payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition'],
                    "attrvalue": old_def
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['first_person_singular'],
                    "attrvalue": "mr_lonely"
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)

        # remove the definition, add 2nd person singular, update 1st person singular, in one request
        new_fps = "what hath god wrought"
        sps_val = "my nose hurts"
        payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['second_person_singular'],
                    "attrvalue": sps_val
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['definition']
                },
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['first_person_singular'],
                    "attrvalue": new_fps
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        fps = list(filter(lambda x: x['attrkey'] == 'first_person_singular', obj['attributes']))[0]
        sps = list(filter(lambda x: x['attrkey'] == 'second_person_singular', obj['attributes']))[0]
        defn = list(filter(lambda x: x['attrkey'] == 'definition', obj['attributes']))[0]

        self.assertEqual(new_fps, fps['attrvalue'])
        self.assertEqual(sps_val, sps['attrvalue'])
        self.assertIsNone(defn['attrvalue'])

    def test_update_delete_same_attr(self):
        # error if we attempt to update and delete the same attr id.
        old_def = "it smells like cereal here"
        attrkey = 'definition'
        attribute_id = self.keyword_mappings['attribute_names_to_ids'][attrkey]
        payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": attribute_id,
                    "attrvalue": old_def
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertEqual(200, r.status_code)

        payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": attribute_id,
                    "attrvalue": "not the same at all"
                },
                {
                    "attribute_id": attribute_id,
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertNotEqual(200, r.status_code)

        r = self.client.get(url_for('api_word.get_word_by_id', word_id=self.word_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        defn = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))[0]
        self.assertEqual(old_def, defn['attrvalue'])

    def test_update_attr_multiple_values(self):
        # trying to update the same attribute with more than one value in one request
        # is not allowed.

        attrkey = 'definition'
        attribute_id = self.keyword_mappings['attribute_names_to_ids'][attrkey]
        payload = {
            js.ATTRIBUTES: [
                {
                    "attribute_id": attribute_id,
                    "attrvalue": "it smells like cereal here"
                },
                {
                    "attribute_id": attribute_id,
                    "attrvalue": "wheee"
                }
            ]
        }

        r = self.client.put(url_for('api_word.update_word', word_id=self.word_id), json=payload)
        self.assertNotEqual(200, r.status_code)
