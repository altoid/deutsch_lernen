import unittest
from dlernen import create_app
from flask import url_for
import json
import random
import string
from pprint import pprint


# make sure that
#
# - valid objects can be created with empty payloads.
# - valid objects can be created with payloads that have null values.
# - create and update both properly set the fields.
# - create and update should return objects that we can verify without having to do a GET.
# - update/batch_delete can properly annul fields.
# - GET and DELETE fucking work.
# - create/POST returns 201 on success.

# cleanup:  word, wordlist, relation
def cleanupWordID(client, word_id):
    client.delete(url_for('api_word.delete_word', word_id=word_id))


def cleanupWordlistID(client, wordlist_id):
    client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=wordlist_id))


def cleanupRelationID(client, relation_id):
    client.delete(url_for('api_relation.delete_relation', relation_id=relation_id))


class TestAPIRelation(unittest.TestCase):
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

        r = cls.client.get(url_for('api_pos.get_pos_keyword_mappings'))
        cls.keyword_mappings = json.loads(r.data)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def createWord(self):
        word = ''.join(random.choices(string.ascii_lowercase, k=10))

        add_payload = {
            "word": word,
            "pos_id": self.keyword_mappings['pos_names_to_ids']['adjective'],
        }
        r = self.client.post(url_for('api_word.add_word'), json=add_payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        word_id = obj['word_id']

        return word, word_id

    #
    # setup:  create 3 dictionary entries.
    #
    def setUp(self):
        self.word1, self.word1_id = self.createWord()
        self.addCleanup(cleanupWordID, self.client, self.word1_id)

        self.word2, self.word2_id = self.createWord()
        self.addCleanup(cleanupWordID, self.client, self.word2_id)

        self.word3, self.word3_id = self.createWord()
        self.addCleanup(cleanupWordID, self.client, self.word3_id)


class TestAPIRelationCreate(TestAPIRelation):
    # null test.  do nothing, just make sure setup works.
    def test_nothing(self):
        pass

    # create an empty relation and then delete it.  make sure it's gone.
    #
    # this is the only test that sends DELETE requests.  the rest of the tests will use addCleanup.
    def test_delete(self):
        payload = {}
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']  # json schema validation ensures this is > 0

        r = self.client.delete(url_for('api_relation.delete_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(404, r.status_code)

    # create an empty relation and make sure its fields are correct.
    def test1_5(self):
        payload = {}
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)

        self.assertIsNone(obj['notes'])
        self.assertIsNone(obj['description'])
        self.assertEqual(0, len(obj['words']))
        self.assertGreater(obj['relation_id'], 0)

    # create an empty relation and make sure its fields are correct when we retrieve it.
    def test1_7(self):
        payload = {}
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        # make sure fields are present but properly empty.
        self.assertIsNone(obj['notes'])
        self.assertIsNone(obj['description'])
        self.assertEqual(0, len(obj['words']))
        self.assertGreater(obj['relation_id'], 0)

    # create an empty relation, using a payload where all fields are specified.  verify that fields are
    # correct on creation and on retrieval.
    def test2(self):
        payload = {
            'word_ids': [],
            'notes': None,
            'description': None
        }

        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        self.assertIsNone(obj['notes'])
        self.assertIsNone(obj['description'])
        self.assertEqual(0, len(obj['words']))

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        # make sure fields are present but properly empty.
        self.assertIsNone(obj['notes'])
        self.assertIsNone(obj['description'])
        self.assertEqual(0, len(obj['words']))

    # create an empty relation, using a payload where description and notes are all whitespace.  both should come
    # back as None.
    def test3(self):
        payload = {
            'word_ids': [],
            'notes': '    ',
            'description': '   '
        }

        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        self.assertIsNone(obj['notes'])
        self.assertIsNone(obj['description'])
        self.assertEqual(0, len(obj['words']))

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        # make sure fields are present but properly empty.
        self.assertIsNone(obj['notes'])
        self.assertIsNone(obj['description'])
        self.assertEqual(0, len(obj['words']))

    # create a bells-and-whistles relation where everything is specified in the payload.
    # verify that fields are correct.
    def test8(self):
        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)

        word_ids = [x['word_id'] for x in obj['words']]
        self.assertEqual(payload['notes'], obj['notes'])
        self.assertEqual(payload['description'], obj['description'])
        self.assertCountEqual(payload['word_ids'], word_ids)
        self.assertGreater(obj['relation_id'], 0)

    # create a bells-and-whistles relation where everything is specified in the payload.
    # verify that fields are correct on retrieval.
    def test8_5(self):
        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        word_ids = [x['word_id'] for x in obj['words']]
        self.assertEqual(payload['notes'], obj['notes'])
        self.assertEqual(payload['description'], obj['description'])
        self.assertCountEqual(payload['word_ids'], word_ids)
        self.assertEqual(relation_id, obj['relation_id'])

    # create two relations and put the same word in both.  retrieve all the
    # relations for that word and verify.
    @unittest.skip
    def test13(self):
        raise NotImplementedError


class TestAPIRelationUpdate(TestAPIRelation):
    # null test.  do nothing, just make sure setup works.
    def test_nothing(self):
        pass

    # create an empty relation and set all the fields via update.  verify.
    def test8(self):
        payload = {}
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.put(url_for('api_relation.update_relation', relation_id=relation_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        word_ids = [x['word_id'] for x in obj['words']]
        self.assertEqual(payload['notes'], obj['notes'])
        self.assertEqual(payload['description'], obj['description'])
        self.assertCountEqual(payload['word_ids'], word_ids)
        self.assertGreater(obj['relation_id'], 0)

    # create an empty relation and set all the fields via update.  verify on retrieval.
    def test8_5(self):
        payload = {}
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.put(url_for('api_relation.update_relation', relation_id=relation_id), json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        word_ids = [x['word_id'] for x in obj['words']]
        self.assertEqual(payload['notes'], obj['notes'])
        self.assertEqual(payload['description'], obj['description'])
        self.assertCountEqual(payload['word_ids'], word_ids)
        self.assertGreater(obj['relation_id'], 0)

    # create a bells-and-whistles relation where everything is specified in the payload.
    # update with empty payload; verify that nothing changed.
    def test9(self):
        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        # update with empty payload
        empty_payload={}
        r = self.client.put(url_for('api_relation.update_relation', relation_id=relation_id), json=empty_payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        # should be unchanged
        word_ids = [x['word_id'] for x in obj['words']]
        self.assertEqual(payload['notes'], obj['notes'])
        self.assertEqual(payload['description'], obj['description'])
        self.assertCountEqual(payload['word_ids'], word_ids)

    # create a bells-and-whistles relation where everything is specified in the payload.
    # update with empty payload; verify ON RETRIEVAL that nothing changed
    def test9_5(self):
        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        # update with empty payload
        empty_payload = {}
        r = self.client.put(url_for('api_relation.update_relation', relation_id=relation_id), json=empty_payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        # should be unchanged
        word_ids = [x['word_id'] for x in obj['words']]
        self.assertEqual(payload['notes'], obj['notes'])
        self.assertEqual(payload['description'], obj['description'])
        self.assertCountEqual(payload['word_ids'], word_ids)

    # create a bells-and-whistles relation where everything is specified in the payload.
    # update everything, verify.
    def test10(self):
        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        update_payload = {
            'word_ids': [self.word3_id],
            'notes': 'do re me',
            'description': 'bleep'
        }
        r = self.client.put(url_for('api_relation.update_relation', relation_id=relation_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        word_ids = [x['word_id'] for x in obj['words']]
        self.assertEqual(update_payload['notes'], obj['notes'])
        self.assertEqual(update_payload['description'], obj['description'])
        self.assertCountEqual([self.word1_id, self.word2_id, self.word3_id], word_ids)

    # create a bells-and-whistles relation where everything is specified in the payload.
    # update everything, verify the update on retrieval.
    def test10_5(self):
        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        update_payload = {
            'word_ids': [self.word3_id],
            'notes': 'do re me',
            'description': 'bleep'
        }
        r = self.client.put(url_for('api_relation.update_relation', relation_id=relation_id), json=update_payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        word_ids = [x['word_id'] for x in obj['words']]
        self.assertEqual(update_payload['notes'], obj['notes'])
        self.assertEqual(update_payload['description'], obj['description'])
        self.assertCountEqual([self.word1_id, self.word2_id, self.word3_id], word_ids)

    # create a bells-and-whistles relation where everything is specified in the payload.
    # nuke everything.  notes/description should come back as None.
    def test12(self):
        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        payload = {
            'notes': None,
            'description': None,
        }
        r = self.client.put(url_for('api_relation.update_relation', relation_id=relation_id), json=payload)
        self.assertEqual(200, r.status_code)

        payload = {
            'word_ids': [self.word1_id, self.word2_id],
        }
        r = self.client.put(url_for('api_relation.delete_from_relation', relation_id=relation_id), json=payload)
        self.assertEqual(200, r.status_code)

        r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        # make sure fields are present but properly empty.
        self.assertIsNone(obj['notes'])
        self.assertIsNone(obj['description'])
        self.assertEqual(0, len(obj['words']))


class TestAPIRelationUpdateWords(TestAPIRelation):
    # null test.  do nothing, just make sure setup works.
    def test_nothing(self):
        pass

    ###  AAAGH parameterize the number of update/delete operations and the lengths of wordlist ids.

    # the classes to test create and update operations on member words should cover the correctness of those
    # operations on the member words of relations.  this class covers cases with redundant update operations,
    # word_ids that don't exist, and batch delete.

    # create a relation with a word that doesn't exist.  relation should be created
    # but have no words.  verify on create.

    # create a relation with a word that doesn't exist.  relation should be created
    # but have no words.  verify on retrieval.

    # create a relation and add a word id that doesn't exist.  shouldn't do anything.  verify on update.

    # create a relation and add a word id that doesn't exist.  shouldn't do anything.  verify on retrieval.

    # create a relation and remove a word id that doesn't exist.  shouldn't do anything.  verify on batch_delete.

    # create a relation and remove a word id that doesn't exist.  shouldn't do anything.  verify on retrieval.

    # create a relation with one word.  remove the word.  verify on batch_delete.

    # create a relation with one word.  remove the word.  verify on retrieval.

    # create a relation with two words.  remove one.  verify on batch_delete.

    # create a relation with two words.  remove one.  verify on retrieval.

    # create a relation with one word.  remove the word and another that exists but is not in the list.  verify on
    # batch_delete.

    # create a relation with one word.  remove the word and another that exists but is not in the list.  verify on
    # retrieval.

    # create a relation with one word.  remove the word and another that does not exist.  verify on update.

    # create a relation with one word.  remove the word and another that does not exist.  verify on retrieval.

    #########

    # do all of the tests above ###### but with each update/batch_delete done twice.

    # do all of the tests above ###### but with each word_id appearing twice in the request.


class TestAPIRelationWordlist(TestAPIRelation):
    # null test.  do nothing, just make sure setup works.
    def test_nothing(self):
        pass

    # create an empty word list and create a relation from it.
    # check everything.
    @unittest.skip
    def test14(self):
        raise NotImplementedError

    # create a standard word list with multiple words and create a relation from it.
    # check everything.
    @unittest.skip
    def test15(self):
        raise NotImplementedError

    # create a smart word list with multiple words and create a relation from it.
    # check everything.
    @unittest.skip
    def test16(self):
        raise NotImplementedError

