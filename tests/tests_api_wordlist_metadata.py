import unittest
import random
import string
import json
from flask import url_for
from dlernen import create_app


def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id, _external=True))


def cleanupWordlistID(client, wordlist_id):
    client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id, _external=True))


class APIWordListMetadataCreate(unittest.TestCase):
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

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    # create a list, name only. get it, verify that fields retrieved are correct.  delete it and make sure it's gone.
    def test_create_1(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        wordlist_id = obj['wordlist_id']

        r = self.client.get(url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertIsNone(obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

        # delete it
        r = self.client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id, _external=True))
        self.assertEqual(r.status_code, 200)

        # make sure it's gone
        r = self.client.get(url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True))
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

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 201)
        obj = json.loads(r.data)
        wordlist_id = obj['wordlist_id']

        r = self.client.get(url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True))
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(citation, obj['citation'])
        self.assertEqual(sqlcode, obj['sqlcode'])
        self.assertEqual('smart', obj['list_type'])

        # delete it
        r = self.client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id, _external=True))
        self.assertEqual(r.status_code, 200)

        # make sure it's gone
        r = self.client.get(url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True))
        self.assertEqual(r.status_code, 404)

    # create a list with no name.  should not succeed.
    def test_create_3(self):
        add_payload = {
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 400)

    # create a list with a bad name.  should not succeed.
    def test_create_4(self):
        add_payload = {
            "name": "  leading and trailing whitespace is verboten  "
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 400)

    # create a list with bad sqlcode.  should not succeed.
    def test_create_5(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        sqlcode = 'bullshit sql'
        add_payload = {
            'name': list_name,
            'sqlcode': sqlcode
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 422)

    # create a list with a bad citation.  should not succeed.
    def test_create_6(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'citation': " "
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
        self.assertEqual(r.status_code, 400)


class APIWordListMetadataUpdate(unittest.TestCase):
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

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

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

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

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

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(sqlcode, obj['sqlcode'])
        self.assertEqual('smart', obj['list_type'])

        sqlcode = 'select id word_id from word where id = 666'

        payload = {
            "sqlcode": sqlcode
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(sqlcode, obj['sqlcode'])
        self.assertEqual('smart', obj['list_type'])

    # add a new list with the same name as in the setup.  should not succeed.
    def test_1_2(self):
        payload = {
            'name': self.list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=payload)
        self.assertNotEqual(r.status_code, 201)

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

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)

        payload = {
            "citation": None,
            "sqlcode": None
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)

        obj = json.loads(r.data)

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(new_name, obj['name'])
        self.assertIsNone(obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

    # update nothing.
    def test_3(self):
        payload = {
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

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

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(new_name, obj['name'])
        self.assertIsNone(obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

        payload = {
            "citation": citation
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

        self.assertEqual(self.wordlist_id, obj['wordlist_id'])
        self.assertEqual(new_name, obj['name'])
        self.assertEqual(citation, obj['citation'])
        self.assertIsNone(obj['sqlcode'])
        self.assertEqual('empty', obj['list_type'])

        payload = {
            "sqlcode": sqlcode,
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = json.loads(r.data)

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

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 400)

    # update the citation to a bullshit value; should not succeed.
    def test_6(self):
        citation = ""

        payload = {
            "citation": citation,
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 400)

    # update the sqlcode to a bullshit value; should not succeed.
    def test_7(self):
        sqlcode = "aoeuieouoeu"

        payload = {
            "sqlcode": sqlcode
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 422)

    # update the name of a standard list but with sqlcode set to None in the payload.  this case broke the UI.
    def test_8_known_word(self):
        # first, make sure the list has stuff in it.

        payload = {
            'words': [
                'haben'
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        result = json.loads(r.data)
        self.assertEqual('standard', result['list_type'])

        new_name = self.list_name + "__RENAMED"
        payload = {
            "name": new_name,
            "citation": None,
            "sqlcode": None
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        result = json.loads(r.data)
        self.assertEqual(new_name, result['name'])
        self.assertEqual('standard', result['list_type'])

    def test_8_unknown_word(self):
        # first, make sure the list has stuff in it.

        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            'words': [
                gibberish
            ]
        }

        r = self.client.put(self.contents_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        result = json.loads(r.data)
        self.assertEqual('standard', result['list_type'])

        new_name = self.list_name + "__RENAMED"
        payload = {
            "name": new_name,
            "citation": None,
            "sqlcode": None
        }

        r = self.client.put(self.metadata_update_url, json=payload)
        self.assertEqual(r.status_code, 200)
        result = json.loads(r.data)
        self.assertEqual(new_name, result['name'])
        self.assertEqual('standard', result['list_type'])

# TODO we will need more tests to deal with update operations on nonempty lists.
