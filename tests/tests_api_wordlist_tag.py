import unittest
from dlernen import create_app
from dlernen import dlernen_json_schema as js
from flask import url_for
import json
import random
import jsonschema
import string
from pprint import pprint


class APIWordlistTag(unittest.TestCase):
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

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist.create_wordlist_metadata', _external=True), json=add_payload)
            obj = json.loads(r.data)
            self.wordlist_id = obj['wordlist_id']

    def tearDown(self):
        with self.app.test_request_context():
            self.client.delete(url_for('api_wordlist.delete_wordlist', wordlist_id=self.wordlist_id,
                                       _external=True))

    # do nothing, just make sure that setUp and tearDown work
    def test_nothing(self):
        pass

    def test_add(self):
        tags = ["eenie", "meenie", "miney", "fart"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)
            # adding tags does not return an object.

    def test_get(self):
        tags = ["eenie", "meenie", "miney", "fart"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            jsonschema.validate(obj, js.WORDLIST_TAG_RESPONSE_SCHEMA)

            self.assertEqual(self.wordlist_id, obj['wordlist_id'])
            self.assertEqual(len(tags), len(obj['tags']))

    def test_update(self):
        tags = ["eenie", "meenie", "miney", "fart"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            update_args = obj['tags'][:2]

            # update the first one and delete the second.
            old_tag = update_args[0]['tag']
            new_tag = old_tag + "_fish_heads"
            updating_tag_id = update_args[0]['wordlist_tag_id']
            deleting_tag_id = update_args[1]['wordlist_tag_id']
            update_args[0]['tag'] = new_tag
            del update_args[1]['tag']

            r = self.client.put(url_for('api_wordlist_tag.update_tags', wordlist_id=self.wordlist_id, _external=True),
                                json=update_args)
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            updated_tags = obj['tags']
            deleted_tag = list(filter(lambda x: x['wordlist_tag_id'] == deleting_tag_id, updated_tags))

            self.assertEqual(len(tags) - 1, len(updated_tags))
            self.assertEqual(0, len(deleted_tag))

            updated_tag = list(filter(lambda x: x['wordlist_tag_id'] == updating_tag_id, updated_tags))[0]
            self.assertEqual(new_tag, updated_tag['tag'])

    def test_delete_nothing(self):
        with self.app.test_request_context():
            tags = []

            r = self.client.put(url_for('api_wordlist_tag.delete_tags', wordlist_id=self.wordlist_id, _external=True),
                                json=tags)
            self.assertEqual(r.status_code, 200)

    def test_delete_all_tags(self):
        tags = ["eenie", "meenie", "miney", "fart"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.put(url_for('api_wordlist_tag.delete_tags', wordlist_id=self.wordlist_id, _external=True),
                                json=[])
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            jsonschema.validate(obj, js.WORDLIST_TAG_RESPONSE_SCHEMA)

            self.assertEqual(self.wordlist_id, obj['wordlist_id'])
            self.assertEqual(0, len(obj['tags']))

    def test_delete_one_tag(self):
        delete_me = "fart"
        tags = ["eenie", "meenie", "miney", delete_me]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.put(url_for('api_wordlist_tag.delete_tags', wordlist_id=self.wordlist_id, _external=True),
                                json=[delete_me])
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            jsonschema.validate(obj, js.WORDLIST_TAG_RESPONSE_SCHEMA)

            self.assertEqual(self.wordlist_id, obj['wordlist_id'])
            self.assertEqual(len(tags) - 1, len(obj['tags']))

    # batch create tags where one of the tags is bad but the rest are good.  NO tags should be created.
    def test_bad_apple(self):
        tags = ["eenie", "meenie", "miney", "illegal tag"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 400)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            jsonschema.validate(obj, js.WORDLIST_TAG_RESPONSE_SCHEMA)

            self.assertEqual(self.wordlist_id, obj['wordlist_id'])
            self.assertEqual(0, len(obj['tags']))

    # batch create tags, then create the same tags again.  the second try should do nothing.
    def test_idempotent(self):
        tags = ["eenie", "meenie", "miney", "fart"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)
            jsonschema.validate(obj, js.WORDLIST_TAG_RESPONSE_SCHEMA)

            self.assertEqual(self.wordlist_id, obj['wordlist_id'])
            self.assertEqual(len(tags), len(obj['tags']))

            tag_ids_1 = {x['wordlist_tag_id'] for x in obj['tags']}

            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)
            jsonschema.validate(obj, js.WORDLIST_TAG_RESPONSE_SCHEMA)

            self.assertEqual(self.wordlist_id, obj['wordlist_id'])
            self.assertEqual(len(tags), len(obj['tags']))

            tag_ids_2 = {x['wordlist_tag_id'] for x in obj['tags']}

            self.assertEqual(tag_ids_1, tag_ids_2)

    # all tag operations must fail if the word list does not exist

    def test_add_tags_bogus_wordlist(self):
        tags = ["eenie", "meenie", "miney", "fart"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=6666666666, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 404)

    def test_get_tags_bogus_wordlist(self):
        with self.app.test_request_context():
            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=6666666666, _external=True))
            self.assertEqual(r.status_code, 404)

    def test_update_tags_bogus_wordlist(self):
        with self.app.test_request_context():
            r = self.client.put(url_for('api_wordlist_tag.update_tags', wordlist_id=6666666666, _external=True),
                                json=[])
            self.assertEqual(r.status_code, 404)

    def test_delete_tags_bogus_wordlist(self):
        with self.app.test_request_context():
            r = self.client.put(url_for('api_wordlist_tag.delete_tags', wordlist_id=6666666666, _external=True),
                                json=[])
            self.assertEqual(r.status_code, 404)

    # update tests

    # tag ids not of this wordlist
    def test_update_bad_tag_ids(self):
        tags = ["eenie", "meenie", "miney", "fart"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            # find the tag with the biggest id.  add 1 to the id and attempt to update.  should give 400.
            update_tags = sorted(obj['tags'], key=lambda x: x['wordlist_tag_id'], reverse=True)
            update_tags[0]['wordlist_tag_id'] += 1

            r = self.client.put(url_for('api_wordlist_tag.update_tags', wordlist_id=self.wordlist_id, _external=True),
                                json=update_tags)
            self.assertEqual(r.status_code, 400)

    # duplicate tag ids
    def test_update_duplicate_tag_ids(self):
        tags = ["eenie", "meenie", "miney", "fart"]

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            # find the tag with the biggest id.  add 1 to the id and attempt to update.  should give 400.
            update_tags = obj['tags'] + obj['tags']

            r = self.client.put(url_for('api_wordlist_tag.update_tags', wordlist_id=self.wordlist_id, _external=True),
                                json=update_tags)
            self.assertEqual(r.status_code, 400)

    # redundant tags should be elided.
    def test_add_duplicate_tags(self):
        tags = ["eenie"] * 3

        with self.app.test_request_context():
            r = self.client.post(url_for('api_wordlist_tag.add_tags', wordlist_id=self.wordlist_id, _external=True),
                                 json=tags)
            self.assertEqual(r.status_code, 200)

            r = self.client.get(url_for('api_wordlist_tag.get_tags', wordlist_id=self.wordlist_id, _external=True))
            self.assertEqual(r.status_code, 200)
            obj = json.loads(r.data)

            self.assertEqual(1, len(obj['tags']))

# TODO - link/unlink tests to add:
#   tag a word, make sure the tag appears when we get the wordlist
#   (create a list with > 1 word to verify ONLY our word got tagged)
#   tag with empty payload - should succeed
#   tag with bogus tag id
#   tag with bogus tag id
#   tag multiple words, untag one, make sure the other is tagged.
#   untag with empty payload - should untag every word that was tagged.
#   ensure that the tags are intact in the tag table
