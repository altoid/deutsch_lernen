import unittest
import jsonschema
import requests
from dlernen import json_schema, config
import json
from pprint import pprint
import random
import string

# {
# 	"word": "verderben",
# 	"word_id": 1234,
# 	"pos_name": "verb",
# 	"attributes": [{
# 			"key": "definition",
# 			"value": "to spoil, deteriorate, go bad"
# sort order is not needed, attributes will be sorted anyway
# 		},
# 		{
# 			"key": "first_person_singular",
# 			"value": "verderbe"
# 		},
# 		{
# 			"key": "key_with_no_set_value",
# 			"value": null
# 		}
# 	]
# }

SAMPLE_WORD_RESULT = {
    "attributes": [
        {
            "key": "article",
            "value": "der"
        },
        {
            "key": "definition",
            "value": "a roast"
        },
        {
            "key": "plural",
            "value": "braten"
        }
    ],
    "pos_name": "Noun",
    "word": "Braten",
    "word_id": 702
}

SAMPLE_WORDLIST_RESULT = {
    "name": "sample_word_list",
    "wordlist_id": 1234,
    "count": 111,
    "is_smart": True
}

SAMPLE_WORDLIST_DETAIL_RESULT = {
    "name": "sample_word_list",
    "wordlist_id": 1234,
    "count": 111,
    "is_smart": True,
    "known_words": [
        {
            "word": "aoeuaeou",
            "word_id": 123,
            "article": "",
            "definition": "hell if i know"
        },
        {
            "word": "Iethdsenihtd",
            "word_id": 465,
            "article": "das",
            "definition": "an odd noun"
        }
    ],
    "source": "where i got this",
    "source_is_url": False,
    "unknown_words": [
        "othuedtiu", "tehuidntuh", "tuehdinteuh"
    ],
    "notes": "lots of stuff"
}


class APITests(unittest.TestCase):
    def test_word_schema(self):
        jsonschema.Draft202012Validator.check_schema(json_schema.WORD_SCHEMA)

    def test_word_sample(self):
        jsonschema.validate(SAMPLE_WORD_RESULT, json_schema.WORD_SCHEMA)

    def test_real_word(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/verderben")
        results = r.json()
        self.assertGreater(len(results), 0)
        for result in results:
            jsonschema.validate(result, json_schema.WORD_SCHEMA)

    def test_wordlist_schema(self):
        jsonschema.Draft202012Validator.check_schema(json_schema.WORDLIST_SCHEMA)

    def test_wordlist_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_RESULT, json_schema.WORDLIST_SCHEMA)

    def test_real_wordlist(self):
        r = requests.get(config.Config.BASE_URL + "/api/wordlists")
        results = r.json()
        self.assertGreater(len(results), 0)
        for result in results:
            jsonschema.validate(result, json_schema.WORDLIST_SCHEMA)

    def test_wordlist_detail_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_DETAIL_RESULT, json_schema.WORDLIST_DETAIL_SCHEMA)

    def test_real_wordlist_detail(self):
        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, 6)
        r = requests.get(url)
        result = r.json()
        jsonschema.validate(result, json_schema.WORDLIST_DETAIL_SCHEMA)

    def test_quiz_data_empty_list_1(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quizkey": "definitions"
        }

        r = requests.put(url, json=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_quiz_data_empty_list_2(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quizkey": "definitions",
            "word_ids": []
        }

        r = requests.put(url, json=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_get_words_empty_list_1(self):
        url = "%s/api/words" % config.Config.DB_URL
        payload = {
        }

        r = requests.put(url, json=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_get_words_empty_list_2(self):
        url = "%s/api/words" % config.Config.DB_URL
        payload = {
            "word_ids": []
        }

        r = requests.put(url, json=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_get_words(self):
        list_ids = [93, 114]
        args = ["list_id=%s" % str(x) for x in list_ids]

        url = "%s/api/choose_words" % config.Config.DB_URL
        url = "%s?limit=%s&%s" % (url, 5, '&'.join(args))
        r = requests.get(url)

        payload = json.loads(r.text)

        url = "%s/api/words" % config.Config.DB_URL
        r = requests.put(url, json=payload)
        results = json.loads(r.text)
        self.assertGreater(len(results), 0)
        for result in results:
            jsonschema.validate(result, json_schema.WORD_SCHEMA)

    def test_wordlist_operations_name_only(self):
        list_name = ''.join(random.choices(string.ascii_lowercase, k=20))

        # create a word list

        create_url = "%s/api/wordlist" % config.Config.DB_URL
        payload = {
            'name': list_name
        }
        r = requests.post(create_url, data=payload)
        result = json.loads(r.text)
        list_id = result['list_id']

        # create new list with same name - should be error
        payload = {
            'name': list_name
        }
        r = requests.post(create_url, data=payload)
        self.assertNotEqual(r.status_code, 200)

        # fetch it

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        self.assertEqual(result['name'], list_name)

        # change the name/source/code

        new_name = ''.join(random.choices(string.ascii_lowercase, k=20))
        source = "confidential"
        payload = {
            'name': new_name,
            'source': source
        }
        r = requests.put(url, data=payload)

        # verify the change

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        self.assertEqual(result['name'], new_name)
        self.assertEqual(result['source'], source)

        # delete the list

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)

        # verify that it's gone

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        self.assertEqual({}, result)

        # delete it again - should do nothing

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)

        # create with same name - should succeed

        create_url = "%s/api/wordlist" % config.Config.DB_URL
        payload = {
            'name': new_name
        }
        r = requests.post(create_url, data=payload)
        self.assertEqual(200, r.status_code)
        result = json.loads(r.text)
        list_id = result['list_id']

        # delete it again

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)

    def test_wordlist_operations_empty_name(self):
        # don't allow create or update with empty name

        # create a word list

        create_url = "%s/api/wordlist" % config.Config.DB_URL
        payload = {
            'name': ''
        }
        r = requests.post(create_url, data=payload)
        self.assertNotEqual(200, r.status_code)

        list_name = ''.join(random.choices(string.ascii_lowercase, k=20))
        payload = {
            'name': list_name
        }
        r = requests.post(create_url, data=payload)
        self.assertEqual(200, r.status_code)
        result = json.loads(r.text)
        list_id = result['list_id']

        # set list name to empty string - should be error

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        payload = {
            'name': ''
        }
        r = requests.put(url, data=payload)
        self.assertNotEqual(r.status_code, 200)

        # make sure the list name wasn't changed

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.get(url)
        result = json.loads(r.text)
        self.assertEqual(list_name, result['name'])

        # clean up

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)



if __name__ == '__main__':
    unittest.main()
