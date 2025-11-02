import unittest
import random
import string
import requests
from dlernen import config


class APIWordListMetadataCreate(unittest.TestCase):
    # create a list, name only. get it, verify that fields retrieved are correct.  delete it and make sure it's gone.
    def test_create_1(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        wordlist_id = obj['wordlist_id']

        r = requests.get("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertIsNone(obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 200)

        # make sure it's gone
        r = requests.get("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 404)

    # create a list with citation and sqlcode set (will be a smart list).  get it, verify that fields
    # retrieved are correct.  delete it and make sure it's gone.
    def test_create_2(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        citation = 'speeding'
        sqlcode = 'select id as word_id from word where id = 111'
        add_payload = {
            'name': list_name,
            'citation': citation,
            'sqlcode': sqlcode
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        wordlist_id = obj['wordlist_id']

        r = requests.get("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(citation, obj['citation'])
        self.assertEqual(sqlcode, obj['sqlcode'])
        self.assertEqual('smart', obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 200)

        # make sure it's gone
        r = requests.get("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 404)

    # create a list with no name.  should not succeed.
    def test_create_3(self):
        add_payload = {
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 400)

    # create a list with a bad name.  should not succeed.
    def test_create_4(self):
        add_payload = {
            "name": "  leading and trailing whitespace is verboten  "
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 400)

    # create a list with bad sqlcode.  should not succeed.
    def test_create_5(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        sqlcode = 'bullshit sql'
        add_payload = {
            'name': list_name,
            'sqlcode': sqlcode
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 422)

    # create a list with a bad citation.  should not succeed.
    def test_create_6(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'citation': " "
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 400)


class APIWordListMetadataUpdate(unittest.TestCase):

    def setUp(self):
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=add_payload)
        obj = r.json()
        self.wordlist_id = obj['wordlist_id']

    def tearDown(self):
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, self.wordlist_id))

    # the setup for this class creates a list with just a name.

    # update the name and set citation and sqlcode to nontrivial values, in a single request.
    # check everything, including list type.
    def test_1(self):
        new_name = self.list_name + "__RENAMED"
        citation = 'speeding'
        sqlcode = 'select id word_id from word where id = 1234'

        payload = {
            "name": new_name,
            "citation": citation,
            "sqlcode": sqlcode
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(new_name, obj['name'])
        self.assertEqual(citation, obj['citation'])
        self.assertEqual(sqlcode, obj['sqlcode'])
        self.assertEqual('smart', obj['list_type'])

    # update the sqlcode to different sqlcode.
    def test_1_1(self):
        sqlcode = 'select id word_id from word where id = 1234'

        payload = {
            "sqlcode": sqlcode
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(sqlcode, obj['sqlcode'])
        self.assertEqual('smart', obj['list_type'])

        sqlcode = 'select id word_id from word where id = 666'

        payload = {
            "sqlcode": sqlcode
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(sqlcode, obj['sqlcode'])
        self.assertEqual('smart', obj['list_type'])

    # add a new list with the same name as in the setup.  should not succeed.
    def test_1_2(self):
        payload = {
            'name': self.list_name
        }

        r = requests.post("%s/api/wordlist/metadata" % config.Config.BASE_URL, json=payload)
        self.assertNotEqual(r.status_code, 200)

    # update all the fields and set citation and sqlcode to nontrivial values, then set citation and sqlcode back to
    # None.
    def test_2(self):
        new_name = self.list_name + "__RENAMED"
        citation = 'speeding'
        sqlcode = 'select id word_id from word where id = 1234'

        payload = {
            "name": new_name,
            "citation": citation,
            "sqlcode": sqlcode
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)

        payload = {
            "citation": None,
            "sqlcode": None
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)

        obj = r.json()

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(new_name, obj['name'])
        self.assertIsNone(obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

    # update nothing.
    def test_3(self):
        payload = {
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(self.list_name, obj['name'])
        self.assertIsNone(obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

    # update all the fields one at a time.
    def test_4(self):
        new_name = self.list_name + "__RENAMED"
        citation = 'speeding'
        sqlcode = 'select id word_id from word where id = 1234'

        payload = {
            "name": new_name,
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(new_name, obj['name'])
        self.assertIsNone(obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

        payload = {
            "citation": citation
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(new_name, obj['name'])
        self.assertEqual(citation, obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

        payload = {
            "sqlcode": sqlcode,
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(new_name, obj['name'])
        self.assertEqual(citation, obj['citation'])
        self.assertEqual(sqlcode, obj['sqlcode'])
        self.assertEqual('smart', obj['list_type'])

    # update the name to a bullshit value; should not succeed.
    def test_5(self):
        new_name = None

        payload = {
            "name": new_name,
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 400)

    # update the citation to a bullshit value; should not succeed.
    def test_6(self):
        citation = ""

        payload = {
            "citation": citation,
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 400)

    # update the sqlcode to a bullshit value; should not succeed.
    def test_7(self):
        sqlcode = "aoeuieouoeu"

        payload = {
            "sqlcode": sqlcode
        }

        r = requests.put("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, self.wordlist_id), json=payload)
        self.assertEqual(r.status_code, 422)

# TODO we will need more tests to deal with update operations on nonempty lists.

