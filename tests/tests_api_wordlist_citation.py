import unittest
import jsonschema
import requests
from dlernen import config
from dlernen import dlernen_json_schema
import random
import string

"""
we've changed the document definition for wordlist metadata:  citation may be null-valued, but if it is a string
it must not have leading or trailing whitespace and it must be of length at least 1.  i.e. no empty strings or 
all-whitespace, and we don't want to have to strip citation strings before writing to the database.

test that this is all well-behaved.
"""

# schema tests:
#
# 1.
# verify that the validator does NOT bitch about properly formed citation values (including NULL).
#
# 2.
# verify that the schema validator complains on malformed citation values.
# - empty string
# - all whitespace
#


class SchemaTests(unittest.TestCase):
    legit_values = [
        None,
        "this is not real sql but matches the pattern in the json schema so shut up",
        "  leading and trailing whitespace   ",
        """

        multiline
        sql
        statement


        """
    ]

    bad_values = [
        "",
        "    ",
        " \t\r\n"
    ]

    def test_legit_values_for_payload(self):
        for citation in self.legit_values:
            with self.subTest(citation=citation):
                payload = {
                    "citation": citation
                }

                jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)

    def test_legit_values_for_response(self):
        for citation in self.legit_values:
            with self.subTest(citation=citation):
                response = {
                    "citation": citation,
                    "wordlist_id": 1,
                    "sqlcode": "aoeu",
                    "name": "aoeu"
                }

                jsonschema.validate(response, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)

    def test_bad_values_for_payload(self):
        for citation in self.bad_values:
            with self.subTest(citation=citation):
                payload = {
                    "citation": citation
                }

                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)

    def test_bad_values_for_response(self):
        for citation in self.bad_values:
            with self.subTest(citation=citation):
                response = {
                    "citation": citation,
                    "wordlist_id": 1,
                    "sqlcode": "oeu",
                    "name": "aoeu"
                }

                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(response, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)


# list create tests
class ListCreate(unittest.TestCase):
    # create a list with just a name.
    # retrieve the metadata.
    # citation should be null.
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

        self.assertIsNone(obj['citation'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with citation explicitly set to null in the payload.
    # retrieve the metadata.
    # citation should be null.
    def test_create_2(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'citation': None
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        # retrieve the metadata
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertIsNone(obj['citation'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with nontrivial citation.
    # retrieve the metadata.
    # inspect the citation and make sure it's what we sent.
    def test_create_3(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        citation = """
        select id as word_id 
        from word 
        where id = 1234"""

        payload = {
            'name': list_name,
            'citation': citation
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        # retrieve the metadata
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(citation, obj['citation'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with illegitimate citation field.
    # the create operation should not succeed.  note that we don't need to test all possibilities of bad values.
    # the validation test will do that.

    def test_create_4(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        citation = " "
        payload = {
            'name': list_name,
            'citation': citation
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertNotEqual(r.status_code, 200)


#
# list update tests
#
class ListUpdate(unittest.TestCase):
    # create a list with no citation.
    # update the citation to some string.
    # retrieve the citation and make sure it's correct.
    def test_update_1(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        citation = 'select id word_id from word where id = 100'
        update_payload = {
            'citation': citation,
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(citation, obj['citation'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with citation.
    # update the name only.
    # retrieve name and citation and make sure they are right.
    def test_update_2(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        citation = 'select id word_id from word where id = 100'

        add_payload = {
            'name': list_name,
            'citation': citation
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
        self.assertEqual(citation, obj['citation'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # create a list with citation.
    # update the citation to null explicitly in the payload.
    # retrieve the citation and make sure it is null.
    #
    def test_update_3(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        citation = 'select id word_id from word where id = 100'

        add_payload = {
            'name': list_name,
            'citation': citation
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'citation': None
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertIsNone(obj['citation'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
