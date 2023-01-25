import unittest
import jsonschema
import requests
from dlernen import dlernen_json_schema, config
import json
from pprint import pprint
import random
import string

SAMPLE_ADDWORD_PAYLOAD = {
    "word": "Tag",  # required, nonempty
    "pos_name": "noun",  # name not id, makes existence check easier
    "attributes": [
        {
            "attrkey": "article",
            "attrvalue": "der"
        },
        {
            "attrkey": "plural",
            "attrvalue": "Tage"
        },
        {
            "attrkey": "definition",
            "attrvalue": "a day"
        }
    ]
}

SAMPLE_UPDATEWORD_PAYLOAD = {
    "word": "blah",  # in case we need to change spelling.  optional.  word id is in the URL.
    "attributes": [  # required but can be empty.
        {
            "attrkey": "article",
            "attrvalue": "der"  # cannot be empty string.
        },
        {
            "attrkey": "plural",
            "attrvalue": "Foofoo"
        }
    ]
}

SAMPLE_WORDS_RESULT = [
    {
        "attributes": [{'attrkey': 'definition',
                        'sort_order': 5,
                        'attrvalue': 'to spoil, deteriorate, go bad'},
                       {'attrkey': 'first_person_singular',
                        'sort_order': 6,
                        'attrvalue': 'verderbe'},
                       {'attrkey': 'second_person_singular',
                        'sort_order': 7,
                        'attrvalue': 'verdirbst'},
                       {'attrkey': 'third_person_singular',
                        'sort_order': 8,
                        'attrvalue': 'verdirbt'},
                       {'attrkey': 'first_person_plural',
                        'sort_order': 9,
                        'attrvalue': 'verderben'},
                       {'attrkey': 'second_person_plural',
                        'sort_order': 10,
                        'attrvalue': 'verderbt'},
                       {'attrkey': 'third_person_plural',
                        'sort_order': 11,
                        'attrvalue': 'verderben'},
                       {'attrkey': 'third_person_past',
                        'sort_order': 16,
                        'attrvalue': 'verdarb'},
                       {'attrkey': 'past_participle',
                        'sort_order': 17,
                        'attrvalue': 'verdorben'}],
        "pos_name": "Verb",
        "word": "verderben",
        "word_id": 2267
    }
]

SAMPLE_WORDIDS_RESULT = {
    "word_ids": [
        1339,
        3429,
        1197,
        3193,
        3086,
        4822,
        1892,
        212,
        3346,
        1616
    ]
}

SAMPLE_WORDLIST_ATTRIBUTE_RESULT = {
    "code": "select distinct word_id\r\nfrom mashup_v\r\nwhere pos_name = 'verb'\r\nand word like '%gehe%'",
    "id": 126,
    "name": "verbs like *geh*",
    "source": ""
}

SAMPLE_WORDLISTS_RESULT = [
    {
        "name": "sample_word_list",
        "wordlist_id": 1234,
        "count": 111,
        "is_smart": True
    }
]

SAMPLE_QUIZ_DATA_RESULT = [
    {
        'quiz_id': 3,
        'word_id': 868,
        'word': 'Tarnung',
        'article': {
            'attrvalue': 'die',
            'attribute_id': 1,
            'correct_count': 0,
            'last_presentation': None,
            'presentation_count': 0,
        },
        'plural': {
            'attrvalue': 'Tarnungen',
            'attribute_id': 3,
            'correct_count': 0,
            'last_presentation': None,
            'presentation_count': 0,
        }
    }
]

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


class APITestsWordGET(unittest.TestCase):
    def test_word_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDS_SCHEMA)

    def test_word_sample(self):
        jsonschema.validate(SAMPLE_WORDS_RESULT, dlernen_json_schema.WORDS_SCHEMA)

    # TODO:  remove this when end-to-end test is implemented
    def test_get_word_by_id(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/14")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDS_SCHEMA)


class APITestsWordPOST(unittest.TestCase):
    # tests for all methods on /api/word
    def test_addword_payload_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.ADDWORD_PAYLOAD_SCHEMA)

    def test_addword_payload_sample(self):
        jsonschema.validate(SAMPLE_ADDWORD_PAYLOAD, dlernen_json_schema.ADDWORD_PAYLOAD_SCHEMA)

    # error conditions:
    # word not in payload
    def test_word_not_in_payload(self):
        payload = {
            "pos_name": "noun",
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)

    # pos not in payload
    def test_pos_not_in_payload(self):
        payload = {
            "word": "aonsetuhasoentuh",
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)

    # attributes not in payload
    def test_attribute_not_in_payload(self):
        payload = {
            "word": "blahblah",
            "pos_name": "noun"
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)

    # payload not json
    # word is 0-length
    def test_zero_length_word(self):
        payload = {
            "word": "",
            "pos_name": "noun",
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)

    # pos is 0-length
    def test_zero_length_pos(self):
        payload = {
            "word": "aeioeauaoeu",
            "pos_name": "",
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)

    # attr keys are bullshit
    def test_bullshit_attrkeys(self):
        payload = {
            "word": "aoeiaoueaou",
            "pos_name": "noun",
            "attributes": [
                {
                    "attrkey": "stinky",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "foofoo",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "legal attrkey here"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)

    # part of speech is bullshit
    def test_bullshit_pos(self):
        payload = {
            "word": "aeioeauaoeu",
            "pos_name": "uiauiauoeu",
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": "der"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthy"
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)


class APITestsWordDelete(unittest.TestCase):
    # deleting nonexistent word_id is not an error
    # real-world delete tests are in the EndToEnd class.
    pass


class APITestsWordPUT(unittest.TestCase):
    def test_updateword_payload_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_updateword_payload_sample(self):
        jsonschema.validate(SAMPLE_UPDATEWORD_PAYLOAD, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)


class APITestsWordEndToEnd(unittest.TestCase):
    # end-to-end test:  add a word, verify existence, update it (attr values and the word itself),
    # verify edits, delete it, verify deletion.

    # another end-to-end test, but without giving any attribute values.

    # adding the same word twice is ok, should have different word ids.

    pass


class APITests(unittest.TestCase):
    def test_list_attribute_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDLIST_ATTRIBUTE_SCHEMA)

    def test_list_attribute_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_ATTRIBUTE_RESULT, dlernen_json_schema.WORDLIST_ATTRIBUTE_SCHEMA)

    def test_real_list_attribute_data(self):
        url = "%s/api/list_attributes/%s" % (config.Config.DB_URL, 126)
        r = requests.get(url)
        result = json.loads(r.text)
        jsonschema.validate(result, dlernen_json_schema.WORDLIST_ATTRIBUTE_SCHEMA)

    def test_quiz_data_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.QUIZ_DATA_SCHEMA)

    def test_quiz_data_sample(self):
        jsonschema.validate(SAMPLE_QUIZ_DATA_RESULT, dlernen_json_schema.QUIZ_DATA_SCHEMA)

    def test_real_quiz_data(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quizkey": "plurals",
            "word_ids": [2175, 3230, 4803]
        }
        r = requests.put(url, json=payload)
        quiz_data = json.loads(r.text)
        jsonschema.validate(quiz_data, dlernen_json_schema.QUIZ_DATA_SCHEMA)

    def test_empty_quiz_data(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quizkey": "plurals",
            "word_ids": []
        }
        r = requests.put(url, json=payload)
        quiz_data = json.loads(r.text)
        jsonschema.validate(quiz_data, dlernen_json_schema.QUIZ_DATA_SCHEMA)

    def test_wordids_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDIDS_SCHEMA)

    def test_wordids_sample(self):
        jsonschema.validate(SAMPLE_WORDIDS_RESULT, dlernen_json_schema.WORDIDS_SCHEMA)

    def test_real_wordids(self):
        r = requests.get(config.Config.BASE_URL + "/api/words/article")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDIDS_SCHEMA)

    def test_get_word_by_word_exact(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/verderben")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDS_SCHEMA)

    def test_get_word_by_word_partial(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/geh?partial=true")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDS_SCHEMA)

    def test_wordlist_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDLISTS_SCHEMA)

    def test_wordlist_sample(self):
        jsonschema.validate(SAMPLE_WORDLISTS_RESULT, dlernen_json_schema.WORDLISTS_SCHEMA)

    def test_real_wordlist(self):
        r = requests.get(config.Config.BASE_URL + "/api/wordlists")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDLISTS_SCHEMA)

    def test_wordlist_detail_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_DETAIL_RESULT, dlernen_json_schema.WORDLIST_DETAIL_SCHEMA)

    def test_real_wordlist_detail(self):
        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, 6)
        r = requests.get(url)
        result = r.json()
        jsonschema.validate(result, dlernen_json_schema.WORDLIST_DETAIL_SCHEMA)

    def test_unreal_wordlist_detail(self):
        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, 6666666)
        r = requests.get(url)
        result = r.json()
        self.assertFalse(bool(result))

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
        args = [str(x) for x in list_ids]

        url = "%s/api/words/plural" % config.Config.DB_URL
        url = "%s?limit=%s&%s" % (url, 5, '&'.join(args))
        url = "%s&list_id=%s" % (url, ','.join(args))

        r = requests.get(url)

        payload = json.loads(r.text)

        url = "%s/api/words" % config.Config.DB_URL
        r = requests.put(url, json=payload)
        results = json.loads(r.text)
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDS_SCHEMA)

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
