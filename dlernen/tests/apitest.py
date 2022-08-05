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

SAMPLE_RESULT = {
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


class MyTestCase(unittest.TestCase):
    def test_schema(self):
        jsonschema.Draft202012Validator.check_schema(json_schema.WORD_SCHEMA)

    def test_sample(self):
        jsonschema.validate(SAMPLE_RESULT, json_schema.WORD_SCHEMA)

    def test_real_word(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/verderben")
        result = r.json()
        self.assertGreater(len(result), 0)
        jsonschema.validate(result[0], json_schema.WORD_SCHEMA)


if __name__ == '__main__':
    unittest.main()
