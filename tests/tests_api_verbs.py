import unittest
import json
from dlernen import create_app
from flask import url_for
from dlernen.dlernen_json_schema import ATTRIBUTES
from dlernen.api_pos import \
    VERB_POS_NAME, \
    SEPARABLE_PREFIX_POS_NAME, \
    INSEPARABLE_PREFIX_POS_NAME
from pprint import pprint
import random
import string


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id))


# tests for separable prefixes:
#
# 1a. create a separable prefix, a grundverb, and a verb that is prefix+grundverb.  fetch by grundverb word id
# 1b. same, but fetch by prefix.
# 2a. same, but don't put the prefix in the dictionary.  fetch by grundverb word id.  should still get something.
# 2b. and by prefix.  should still get something.
# 3a. put a prefix and a grundverb into the dictionary but no combination of them.  fetch by prefix; should be nothing.
# 3b. same, but fetch by grundverb id.  should be nothing.
#
# we'll have to add a third_person_singular for each verb we create or else they won't appear in the view.
class TestVerbsSeparablePrefixes(unittest.TestCase):
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

    def add_prefix(self, prefix):
        payload = {
            'word': prefix,
            'pos_id': self.keyword_mappings['pos_names_to_ids'][SEPARABLE_PREFIX_POS_NAME]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        prefix_word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, prefix_word_id)

        return prefix_word_id

    def add_verb(self, verb, prefix=""):
        payload = {
            'word': prefix + verb,
            'pos_id': self.keyword_mappings['pos_names_to_ids'][VERB_POS_NAME],
        }

        if prefix:
            payload[ATTRIBUTES] = [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['third_person_singular'],
                    "attrvalue": "%s %s" % (verb, prefix)
                }
            ]

        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        return word_id

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    def test1a(self):
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        prefix_word_id = self.add_prefix(prefix)
        grundverb_word_id = self.add_verb(grundverb)
        word_id = self.add_verb(grundverb, prefix)

        r = self.client.get(url_for('api_verbs.get_verbs_by_grundverb',
                                    grundverb=grundverb))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        s = obj[0]
        control = {
            'prefix_word_id': prefix_word_id,
            'prefix': prefix,
            'word_id': word_id,
            'grundverb_word_id': grundverb_word_id,
            'prefix_pos_name': SEPARABLE_PREFIX_POS_NAME
        }
        self.assertEqual(1, len(obj))
        self.assertDictEqual(control, s)

    def test1b(self):
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        prefix_word_id = self.add_prefix(prefix)
        grundverb_word_id = self.add_verb(grundverb)
        word_id = self.add_verb(grundverb, prefix)

        r = self.client.get(url_for('api_verbs.get_verbs_by_prefix',
                                    prefix=prefix))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        s = obj[0]
        control = {
            'prefix_word_id': prefix_word_id,
            'prefix': prefix,
            'word_id': word_id,
            'grundverb_word_id': grundverb_word_id,
            'prefix_pos_name': SEPARABLE_PREFIX_POS_NAME
        }
        self.assertEqual(1, len(obj))
        self.assertDictEqual(control, s)

    def test2a(self):
        # prefix will not be put into the dictionary.
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        grundverb_word_id = self.add_verb(grundverb)
        word_id = self.add_verb(grundverb, prefix)

        r = self.client.get(url_for('api_verbs.get_verbs_by_grundverb',
                                    grundverb=grundverb))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        s = obj[0]
        control = {
            'prefix_word_id': None,
            'prefix': prefix,
            'word_id': word_id,
            'grundverb_word_id': grundverb_word_id,
            'prefix_pos_name': SEPARABLE_PREFIX_POS_NAME
        }
        self.assertEqual(1, len(obj))
        self.assertDictEqual(control, s)

    def test2b(self):
        # prefix will not be put into the dictionary.
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        grundverb_word_id = self.add_verb(grundverb)
        word_id = self.add_verb(grundverb, prefix)

        r = self.client.get(url_for('api_verbs.get_verbs_by_prefix',
                                    prefix=prefix))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        s = obj[0]
        control = {
            'prefix_word_id': None,
            'prefix': prefix,
            'word_id': word_id,
            'grundverb_word_id': grundverb_word_id,
            'prefix_pos_name': SEPARABLE_PREFIX_POS_NAME
        }
        self.assertEqual(1, len(obj))
        self.assertDictEqual(control, s)

    def test3a(self):
        # - put a prefix and a grundverb into the dictionary but no combination of them.
        # fetch by grundverb id; should be nothing.
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        prefix_word_id = self.add_prefix(prefix)
        grundverb_word_id = self.add_verb(grundverb)

        r = self.client.get(url_for('api_verbs.get_verbs_by_grundverb',
                                    grundverb=grundverb))
        self.assertEqual(404, r.status_code)

    def test3b(self):
        # - put a prefix and a grundverb into the dictionary but no combination of them.
        # fetch by prefix; should be nothing.
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        prefix_word_id = self.add_prefix(prefix)
        grundverb_word_id = self.add_verb(grundverb)

        r = self.client.get(url_for('api_verbs.get_verbs_by_prefix',
                                    prefix=prefix))
        self.assertEqual(404, r.status_code)


# tests for inseparable prefixes:
# - create a prefix, a grundverb, and a verb that is prefix+grundverb.  fetch by grundverb word id
# - same, but fetch by prefix.
# - same, but don't put the prefix in the dictionary.  fetch by grundverb word id.  should be nothing.
# - and by prefix.  should be nothing.
# - put a prefix and a grundverb into the dictionary but no combination of them.  fetch by prefix; should be nothing.
# - same, but fetch by grundverb id.  should be nothing.

class TestVerbsInseparablePrefixes(unittest.TestCase):
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

    def add_prefix(self, prefix):
        payload = {
            'word': prefix,
            'pos_id': self.keyword_mappings['pos_names_to_ids'][INSEPARABLE_PREFIX_POS_NAME]
        }
        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        prefix_word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, prefix_word_id)

        return prefix_word_id

    def add_verb(self, verb, prefix=""):
        payload = {
            'word': prefix + verb,
            'pos_id': self.keyword_mappings['pos_names_to_ids'][VERB_POS_NAME],
            ATTRIBUTES: [
                {
                    "attribute_id": self.keyword_mappings['attribute_names_to_ids']['third_person_singular'],
                    "attrvalue": prefix + verb
                }
            ]
        }

        r = self.client.post(url_for('api_word.add_word'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        word_id = obj['word_id']
        self.addCleanup(cleanupWordID, self.client, word_id)

        return word_id

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    def test1a(self):
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        prefix_word_id = self.add_prefix(prefix)
        grundverb_word_id = self.add_verb(grundverb)
        word_id = self.add_verb(grundverb, prefix)

        r = self.client.get(url_for('api_verbs.get_verbs_by_grundverb',
                                    grundverb=grundverb))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        s = obj[0]
        control = {
            'prefix_word_id': prefix_word_id,
            'prefix': prefix,
            'word_id': word_id,
            'grundverb_word_id': grundverb_word_id,
            'prefix_pos_name': INSEPARABLE_PREFIX_POS_NAME
        }
        self.assertEqual(1, len(obj))
        self.assertDictEqual(control, s)

    def test1b(self):
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        prefix_word_id = self.add_prefix(prefix)
        grundverb_word_id = self.add_verb(grundverb)
        word_id = self.add_verb(grundverb, prefix)

        r = self.client.get(url_for('api_verbs.get_verbs_by_prefix',
                                    prefix=prefix))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        s = obj[0]
        control = {
            'prefix_word_id': prefix_word_id,
            'prefix': prefix,
            'word_id': word_id,
            'grundverb_word_id': grundverb_word_id,
            'prefix_pos_name': INSEPARABLE_PREFIX_POS_NAME
        }
        self.assertEqual(1, len(obj))
        self.assertDictEqual(control, s)

    def test2a(self):
        # prefix will not be put into the dictionary.
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        grundverb_word_id = self.add_verb(grundverb)
        word_id = self.add_verb(grundverb, prefix)

        r = self.client.get(url_for('api_verbs.get_verbs_by_grundverb',
                                    grundverb=grundverb))
        self.assertEqual(404, r.status_code)

    def test2b(self):
        # prefix will not be put into the dictionary.
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        grundverb_word_id = self.add_verb(grundverb)
        word_id = self.add_verb(grundverb, prefix)

        r = self.client.get(url_for('api_verbs.get_verbs_by_prefix',
                                    prefix=prefix))
        self.assertEqual(404, r.status_code)

    def test3a(self):
        # - put a prefix and a grundverb into the dictionary but no combination of them.
        # fetch by grundverb id; should be nothing.
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        prefix_word_id = self.add_prefix(prefix)
        grundverb_word_id = self.add_verb(grundverb)

        r = self.client.get(url_for('api_verbs.get_verbs_by_grundverb',
                                    grundverb=grundverb))
        self.assertEqual(404, r.status_code)

    def test3b(self):
        # - put a prefix and a grundverb into the dictionary but no combination of them.
        # fetch by prefix; should be nothing.
        grundverb = ''.join(random.choices(string.ascii_lowercase, k=10))
        prefix = ''.join(random.choices(string.ascii_lowercase, k=5))

        prefix_word_id = self.add_prefix(prefix)
        grundverb_word_id = self.add_verb(grundverb)

        r = self.client.get(url_for('api_verbs.get_verbs_by_prefix',
                                    prefix=prefix))
        self.assertEqual(404, r.status_code)
