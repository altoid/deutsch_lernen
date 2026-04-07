import unittest
from dlernen import create_app
from flask import url_for
import json
import random
import string
from parameterized import parameterized
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

    def createRelation(self, word_ids):
        payload = {
            'word_ids': word_ids
        }

        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']

        return relation_id

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

    # make sure an invalid payload returns a 400
    def test_garbage_payload(self):
        payload = {
            'bull': 'shit'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(400, r.status_code)

    # create an empty relation and make sure its fields are correct.
    def test1_5(self):
        payload = {}
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        self.addCleanup(cleanupRelationID, self.client, obj['relation_id'])

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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
        self.addCleanup(cleanupRelationID, self.client, obj['relation_id'])

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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


class TestAPIRelationParameterized(TestAPIRelation):
    def test_nothing(self):
        pass

    # create a relation with redundant word ids and see that everything is well-behaved.
    # mostly an exercise in using parameterized.
    @parameterized.expand(
        [
            (1, False),
            (3, True)
        ]
    )
    def test12(self, nrepeats, validate_on_retrieval):
        payload = {
            'word_ids': [self.word1_id] * nrepeats
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']
        self.addCleanup(cleanupRelationID, self.client, relation_id)

        if validate_on_retrieval:
            r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
            self.assertEqual(200, r.status_code)
            obj = json.loads(r.data)

        word_ids = [x['word_id'] for x in obj['words']]
        self.assertCountEqual([self.word1_id], word_ids)


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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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

    # create an empty relation attempt to update with an invalid payload.
    def test_garbage_payload(self):
        payload = {}
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']
        self.addCleanup(cleanupRelationID, self.client, relation_id)

        payload = {
            'crackers': 'wheat thins'
        }
        r = self.client.put(url_for('api_relation.update_relation', relation_id=relation_id), json=payload)
        self.assertEqual(400, r.status_code)

    # create an empty relation and set all the fields via update.  verify on retrieval.
    def test8_5(self):
        payload = {}
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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
        self.addCleanup(cleanupRelationID, self.client, relation_id)

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

    # attempt to delete from a relation by using a bad payload.
    def test_garbage_delete_payload(self):
        payload = {
            'word_ids': [self.word1_id, self.word2_id],
            'notes': 'cinnamon and cheese',
            'description': 'smells funny'
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']
        self.addCleanup(cleanupRelationID, self.client, relation_id)

        payload = {
            'bovine': 'excrement'
        }
        r = self.client.put(url_for('api_relation.delete_from_relation', relation_id=relation_id), json=payload)
        self.assertEqual(400, r.status_code)


class TestAPIRelationUpdateWords(TestAPIRelation):
    # null test.  do nothing, just make sure setup works.
    def test_nothing(self):
        pass

    # AAAGH parameterize the number of update/delete operations and the lengths of wordlist ids.

    # the classes to test create and update operations on member words should cover the correctness of those
    # operations on the member words of relations.  this class covers cases with redundant update and delete
    # operations, redundant word_ids, and word_ids that don't exist.

    # perform the following tests.  for each, verify the result of the tested operation and on a subsequent retrieval
    # of the relation.

    # create a relation with a word that doesn't exist.  relation should be created
    # but have no words.

    # create a relation and add a word id that doesn't exist.  shouldn't do anything.

    # create a relation and remove a word id that doesn't exist.  shouldn't do anything.

    # create a relation with one word.  remove the word.
    @parameterized.expand(
        [
            (1, False),
            (2, True)
        ]
    )
    def test12(self, remove_n_times, validate_on_retrieval):
        payload = {
            'word_ids': [self.word1_id]
        }
        r = self.client.post(url_for('api_relation.create_relation'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        relation_id = obj['relation_id']
        self.addCleanup(cleanupRelationID, self.client, relation_id)

        for _ in range(remove_n_times):
            payload = {
                'word_ids': [self.word1_id]
            }
            r = self.client.put(url_for('api_relation.delete_from_relation', relation_id=relation_id), json=payload)
            self.assertEqual(200, r.status_code)
            obj = json.loads(r.data)

        if validate_on_retrieval:
            r = self.client.get(url_for('api_relation.get_relation', relation_id=relation_id))
            self.assertEqual(200, r.status_code)
            obj = json.loads(r.data)

        self.assertEqual(0, len([x['word_id'] for x in obj['words']]))

    # create a relation with two words.  remove one.

    # create a relation with one word.  remove the word and another that exists but is not in the list.

    # create a relation with one word.  remove the word and another that does not exist.


class TestAPIRelationWordlist(TestAPIRelation):
    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # non-existent wordlist
    def test0(self):
        r = self.client.get(url_for('api_wordlist.get_relations', wordlist_id=666666))
        self.assertEqual(404, r.status_code)

    # create an empty wordlist and verify that api_wordlist.get_relations is well-behaved.
    def test1(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id)

        r = self.client.get(url_for('api_wordlist.get_relations', wordlist_id=wordlist_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        self.assertIsNotNone(obj)
        self.assertEqual(0, len(obj))

    # create 10 words.  put 0-5 into a STANDARD wordlist and 7-10 are free-floating.
    # create a relation with 0 1 2, another with 4 5 6, another with 5 6 7.
    # retrieve them all with api_wordlist.get_relations and verify.
    def test2(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id)

        # create the words
        word_ids = [self.word1_id, self.word2_id, self.word3_id]
        for _ in range(7):
            _, word_id = self.createWord()
            word_ids.append(word_id)

        # add the words to the word list
        payload = {
            'word_ids': word_ids[0:6]
        }

        r = self.client.put(url_for('api_wordlist.update_wordlist_contents', wordlist_id=wordlist_id),
                            json=payload)
        self.assertEqual(200, r.status_code)

        # create the relations
        relation1_id = self.createRelation(word_ids[0:3])
        self.addCleanup(cleanupRelationID, self.client, relation1_id)

        relation2_id = self.createRelation(word_ids[4:7])
        self.addCleanup(cleanupRelationID, self.client, relation2_id)

        relation3_id = self.createRelation(word_ids[5:8])
        self.addCleanup(cleanupRelationID, self.client, relation3_id)

        # do the stuff
        r = self.client.get(url_for('api_wordlist.get_relations', wordlist_id=wordlist_id))
        self.assertEqual(200, r.status_code)
        relation_arr = json.loads(r.data)

        control = [relation1_id, relation2_id, relation3_id]
        experiment = [x['relation_id'] for x in relation_arr]

        self.assertCountEqual(control, experiment)

    # create 10 words.  put 1-6 into a SMART wordlist and 7-10 are free-floating.
    # create a relation with 1 2 3, another with 5 6 7, another with 6 7 8.
    # retrieve them all with api_wordlist.get_relations and verify.
    def test3(self):
        # create the words
        word_ids = [self.word1_id, self.word2_id, self.word3_id]
        for _ in range(7):
            _, word_id = self.createWord()
            word_ids.append(word_id)

        # create the (smart) list
        word_id_args = word_ids[0:6]
        args = ','.join(list(map(str, word_id_args)))
        sqlcode = """
        select id word_id from word
        where id in (%(args)s)
        """ % {'args': args}

        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'sqlcode': sqlcode
        }

        r = self.client.post(url_for('api_wordlist.create_wordlist_metadata'), json=payload)
        self.assertEqual(201, r.status_code)
        obj = json.loads(r.data)
        wordlist_id = obj['wordlist_id']
        self.addCleanup(cleanupWordlistID, self.client, wordlist_id)

        # create the relations
        relation1_id = self.createRelation(word_ids[0:3])
        self.addCleanup(cleanupRelationID, self.client, relation1_id)

        relation2_id = self.createRelation(word_ids[4:7])
        self.addCleanup(cleanupRelationID, self.client, relation2_id)

        relation3_id = self.createRelation(word_ids[5:8])
        self.addCleanup(cleanupRelationID, self.client, relation3_id)

        # do the stuff
        r = self.client.get(url_for('api_wordlist.get_relations', wordlist_id=wordlist_id))
        self.assertEqual(200, r.status_code)
        relation_arr = json.loads(r.data)

        control = [relation1_id, relation2_id, relation3_id]
        experiment = [x['relation_id'] for x in relation_arr]

        self.assertCountEqual(control, experiment)
        self.assertEqual(3, len(relation_arr[0]['words']))
        self.assertEqual(3, len(relation_arr[1]['words']))
        self.assertEqual(3, len(relation_arr[2]['words']))


class TestAPIRelationWord(TestAPIRelation):
    # tests for api_word.get_relations

    # do nothing, just make sure that setUp works
    def test_nothing(self):
        pass

    # non-existent word
    def test1(self):
        r = self.client.get(url_for('api_word.get_relations', word_id=666666))
        self.assertEqual(404, r.status_code)

    # unaffiliated word
    def test2(self):
        r = self.client.get(url_for('api_word.get_relations', word_id=self.word1_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)
        self.assertEqual(0, len(obj))

    def test3(self):
        relation1_id = self.createRelation([self.word1_id])
        self.addCleanup(cleanupRelationID, self.client, relation1_id)

        relation2_id = self.createRelation([self.word1_id])
        self.addCleanup(cleanupRelationID, self.client, relation2_id)

        r = self.client.get(url_for('api_word.get_relations', word_id=self.word1_id))
        self.assertEqual(200, r.status_code)
        obj = json.loads(r.data)

        control = [relation1_id, relation2_id]
        experiment = [x['relation_id'] for x in obj]

        self.assertCountEqual(control, experiment)
