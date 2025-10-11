import unittest
import jsonschema
import requests
from dlernen import config
from dlernen import dlernen_json_schema
import json
import random
import string

"""
we've changed the document definition for wordlist metadata:  sqlcode may be null-valued, but if it is a string
it must not have leading or trailing whitespace and it must be of length at least 1.  i.e. no empty strings or 
all-whitespace, and we don't want to have to strip sqlcode strings before writing to the database.

test that this is all well-behaved.

testing list behavior when the sqlcode field is changed is not in the scope of this test class.
e.g.  updating the sqlcode field of a standard list should not succeed (since there are words in it),
but these behavioral tests are already implemented elsewhere.  the purpose of this class is just to make sure
the api is sane in the presense of the json doc changes.
"""

# schema tests:
#
# 1.
# verify that the validator does NOT bitch about properly formed sqlcode values (including NULL).
#
# 2.
# verify that the schema validator complains on malformed sqlcode values.
# - empty string
# - leading whitespace
# - trailing whitespace
#
#


class SchemaTests(unittest.TestCase):
    def test_legit_value_1(self):
        payload = {
            "sqlcode": None
        }

        jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)

    def test_legit_value_2(self):
        payload = {
            "sqlcode": "this is not real sql but matches the pattern in the json schema so shut up"
        }

        jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)

    def test_legit_value_3(self):
        response = {
            "sqlcode": None,
            "wordlist_id": 1,
            "citation": "oeu",
            "name": "aoeu"
        }

        jsonschema.validate(response, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)

    def test_legit_value_4(self):
        response = {
            "sqlcode": "this is not real sql but matches the pattern in the json schema so shut up",
            "wordlist_id": 1,
            "citation": "oeu",
            "name": "aoeu"
        }

        jsonschema.validate(response, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)

    def test_bad_value_1(self):
        payload = {
            "sqlcode": ""
        }

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)

    def test_bad_value_2(self):
        payload = {
            "sqlcode": "trailing whitespace  "
        }

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)

    def test_bad_value_3(self):
        payload = {
            "sqlcode": "  leading whitespace"
        }

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)

    def test_bad_value_4(self):
        response = {
            "sqlcode": "",
            "wordlist_id": 1,
            "citation": "oeu",
            "name": "aoeu"
        }

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(response, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)

    def test_bad_value_5(self):
        response = {
            "sqlcode": "trailing whitespace  ",
            "wordlist_id": 1,
            "citation": "oeu",
            "name": "aoeu"
        }

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(response, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)

    def test_bad_value_6(self):
        response = {
            "sqlcode": "  leading whitespace",
            "wordlist_id": 1,
            "citation": "oeu",
            "name": "aoeu"
        }

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(response, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)


# list create tests
class ListCreate(unittest.TestCase):
    # create a list with just a name.
    # retrieve the metadata.
    # sqlcode should be null.
    def test_create_1(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        # retrieve the metadata
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertIsNone(obj['sqlcode'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with sqlcode explicitly set to null in the payload.
    # retrieve the metadata.
    # sqlcode should be null.
    def test_create_2(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'sqlcode': None
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        # retrieve the metadata
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertIsNone(obj['sqlcode'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with nontrivial sqlcode.
    # retrieve the metadata.
    # inspect the sqlcode and make sure it's what we sent.
    def test_create_3(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        sqlcode = "select id as word_id from word where id = 1234"
        payload = {
            'name': list_name,
            'sqlcode': sqlcode
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        # retrieve the metadata
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(sqlcode, obj['sqlcode'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with illegitimate sqlcode field.
    # the create operation should not succeed.  note that we don't need to test all possibilities of bad values.
    # the validation test will do that.

    def test_create_4(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        sqlcode = " "
        payload = {
            'name': list_name,
            'sqlcode': sqlcode
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertNotEqual(r.status_code, 200)


#
# list update tests
#
class ListUpdate(unittest.TestCase):
    # create a list with no sqlcode.
    # update the sqlcode to some string.
    # retrieve the sqlcode and make sure it's correct.
    def test_update_1(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        sqlcode = 'select id word_id from word where id = 100'
        update_payload = {
            'sqlcode': sqlcode,
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(sqlcode, obj['sqlcode'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with sqlcode.
    # update the name only.
    # retrieve name and sqlcode and make sure they are right.
    def test_update_2(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        sqlcode = 'select id word_id from word where id = 100'

        add_payload = {
            'name': list_name,
            'sqlcode': sqlcode
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        list_name = list_name + "__RENAMED"
        update_payload = {
            'name': list_name
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(list_name, obj['name'])
        self.assertEqual(sqlcode, obj['sqlcode'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with sqlcode.
    # update the sqlcode to null explicitly in the payload.
    # retrieve the sqlcode and make sure it is null.
    #
    def test_update_3(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        sqlcode = 'select id word_id from word where id = 100'

        add_payload = {
            'name': list_name,
            'sqlcode': sqlcode
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'sqlcode': None
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertIsNone(obj['sqlcode'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
