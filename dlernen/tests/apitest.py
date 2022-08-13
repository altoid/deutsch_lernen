import unittest
import jsonschema
import requests
from dlernen import json_schema, config
import json
from pprint import pprint

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

        r = requests.put(url, data=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_quiz_data_empty_list_2(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quizkey": "definitions",
            "word_ids": "[]"
        }

        r = requests.put(url, data=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_get_words_empty_list_1(self):
        url = "%s/api/words" % config.Config.DB_URL
        payload = {
        }

        r = requests.put(url, data=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_get_words_empty_list_2(self):
        url = "%s/api/words" % config.Config.DB_URL
        payload = {
            "word_ids": "[]"
        }

        r = requests.put(url, data=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_get_words(self):
        url = "%s/api/choose_words" % config.Config.DB_URL
        url = "%s?limit=%s&list_ids=%s" % (url, 5, "93,114")
        r = requests.get(url)

        payload = json.loads(r.text)
        payload['word_ids'] = json.dumps(payload['word_ids'])

        url = "%s/api/words" % config.Config.DB_URL
        r = requests.put(url, data=payload)
        results = json.loads(r.text)
        self.assertGreater(len(results), 0)
        for result in results:
            jsonschema.validate(result, json_schema.WORD_SCHEMA)


if __name__ == '__main__':
    unittest.main()
