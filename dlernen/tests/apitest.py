import unittest
import jsonschema
import requests
from dlernen import json_schema, config

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


class MyTestCase(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
