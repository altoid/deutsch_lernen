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

SAMPLE_ADDATTRIBUTES_PAYLOAD = {
    "attributes": [
        {
            "attrkey": "article",
            "attrvalue": "der"
        },
        {
            "attrkey": "plural",
            "attrvalue": "Blahs"
        }
    ]
}

SAMPLE_UPDATEWORD_PAYLOAD = {
    "word": "blah",  # in case we need to change spelling.  optional.  word id is in the URL.
    "attributes": [  # required but can be empty.
        {
            "attrvalue_id": 444,
            "attrvalue": "der"  # cannot be empty string.
        },
        {
            "attrvalue_id": 555,
            "attrvalue": "Foofoo"
        }
    ]
}

SAMPLE_WORDS_RESULT = [
    {
        "attributes": [{'attrkey': 'definition',
                        'sort_order': 5,
                        'attrvalue_id': 123,
                        'attrvalue': 'to spoil, deteriorate, go bad'},
                       {'attrkey': 'first_person_singular',
                        'sort_order': 6,
                        'attrvalue_id': 123,
                        'attrvalue': 'verderbe'},
                       {'attrkey': 'second_person_singular',
                        'sort_order': 7,
                        'attrvalue_id': 123,
                        'attrvalue': 'verdirbst'},
                       {'attrkey': 'third_person_singular',
                        'sort_order': 8,
                        'attrvalue_id': 123,
                        'attrvalue': 'verdirbt'},
                       {'attrkey': 'first_person_plural',
                        'sort_order': 9,
                        'attrvalue_id': 123,
                        'attrvalue': 'verderben'},
                       {'attrkey': 'second_person_plural',
                        'sort_order': 10,
                        'attrvalue_id': 123,
                        'attrvalue': 'verderbt'},
                       {'attrkey': 'third_person_plural',
                        'sort_order': 11,
                        'attrvalue_id': 123,
                        'attrvalue': 'verderben'},
                       {'attrkey': 'third_person_past',
                        'sort_order': 16,
                        'attrvalue_id': 123,
                        'attrvalue': 'verdarb'},
                       {'attrkey': 'past_participle',
                        'sort_order': 17,
                        'attrvalue_id': 123,
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


class SchemaTests(unittest.TestCase):
    """
    checks on json schema objects are all done in one class here.

    we do this because we don't want to do this in test classes that have setup and teardown methods
    which depend on these schema definitions being correct.
    """

    def test_word_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDS_SCHEMA)

    def test_word_sample(self):
        jsonschema.validate(SAMPLE_WORDS_RESULT, dlernen_json_schema.WORDS_SCHEMA)

    def test_addword_payload_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.ADDWORD_PAYLOAD_SCHEMA)

    def test_addword_payload_sample(self):
        jsonschema.validate(SAMPLE_ADDWORD_PAYLOAD, dlernen_json_schema.ADDWORD_PAYLOAD_SCHEMA)

    def test_updateword_payload_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_updateword_payload_sample(self):
        jsonschema.validate(SAMPLE_UPDATEWORD_PAYLOAD, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_add_attributes_payload_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.ADDATTRIBUTES_PAYLOAD_SCHEMA)

    def test_add_attributes_payload_sample(self):
        jsonschema.validate(SAMPLE_ADDATTRIBUTES_PAYLOAD, dlernen_json_schema.ADDATTRIBUTES_PAYLOAD_SCHEMA)

    def test_list_attribute_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDLIST_ATTRIBUTE_SCHEMA)

    def test_list_attribute_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_ATTRIBUTE_RESULT, dlernen_json_schema.WORDLIST_ATTRIBUTE_SCHEMA)

    def test_quiz_data_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.QUIZ_DATA_SCHEMA)

    def test_quiz_data_sample(self):
        jsonschema.validate(SAMPLE_QUIZ_DATA_RESULT, dlernen_json_schema.QUIZ_DATA_SCHEMA)

    def test_wordids_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDIDS_SCHEMA)

    def test_wordids_sample(self):
        jsonschema.validate(SAMPLE_WORDIDS_RESULT, dlernen_json_schema.WORDIDS_SCHEMA)

    def test_wordlist_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDLISTS_SCHEMA)

    def test_wordlist_sample(self):
        jsonschema.validate(SAMPLE_WORDLISTS_RESULT, dlernen_json_schema.WORDLISTS_SCHEMA)

    def test_wordlist_detail_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDLIST_DETAIL_SCHEMA)

    def test_wordlist_detail_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_DETAIL_RESULT, dlernen_json_schema.WORDLIST_DETAIL_SCHEMA)


class APITestsWordGET(unittest.TestCase):
    # TODO implement tests here
    pass


class APITestsWordPOST(unittest.TestCase):
    # tests for all methods on /api/word
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
    def test_payload_not_json(self):
        payload = "this is some bullshit right here"
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)

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

    # 0-length attribute
    def test_zero_length_attrvalue(self):
        payload = {
            "word": "aeioeauaoeu",
            "pos_name": "noun",
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": ""
                }
            ]
        }
        r = requests.post(config.Config.BASE_URL + "/api/word", data=payload)
        self.assertNotEqual(r.status_code, 200)


class APITestsWordPUT(unittest.TestCase):
    # TODO:  implement tests for error conditions:
    # bullshit word id
    # missing word is ok.
    # attr ids that don't belong to the word.
    # zero-length word
    # zero-length attribute value
    # payload not json
    pass

# TODO:  make sure proper cleanup happens if any assertions fail on status code values.  setup/teardown?

# TODO:  wordlist tests go in their own class


class APITestsWordEndToEnd(unittest.TestCase):
    # end-to-end test:  add a word, verify existence, update it (attr values and the word itself),
    # verify edits, delete it, verify deletion.  delete it again, should be no errors.

    def test_basic(self):
        add_payload = {
            "word": "end_to_end_test1",
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
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id = obj['word_id']

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        self.assertTrue('word_id' in obj)

        victim = obj['attributes'][0]['attrvalue_id']
        new_value = 'changed to this'
        new_word = 'respell_word_succeeded'
        update_payload = {
            'word': new_word,
            'attributes': [
                {
                    'attrvalue_id': victim,
                    'attrvalue': new_value
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(new_word, obj['word'])
        a = list(filter(lambda x: x['attrvalue_id'] == victim, obj['attributes']))
        self.assertEqual(1, len(a))
        self.assertEqual(new_value, a[0]['attrvalue'])

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        obj = r.json()
        self.assertTrue('word_id' not in obj)

        # delete it again, should not cause error
        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

    # another end-to-end test, but without giving any attribute values.  add attributes to the word.  retrieve
    # word, new attributes should be there.
    def test_add_attrs(self):
        add_payload = {
            "word": "test_add_attrs",
            "pos_name": "noun",
            "attributes": [
                # {
                #     "attrkey": "article",
                #     "attrvalue": "der"
                # },
                # {
                #     "attrkey": "plural",
                #     "attrvalue": "Xxxxxxxxxx"
                # },
                # {
                #     "attrkey": "definition",
                #     "attrvalue": "feelthy"
                # }
            ]
        }
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id = obj['word_id']

        add_attr_payload = {
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

        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, word_id), json=add_attr_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        attrdict = {r['attrkey']: r['attrvalue'] for r in obj['attributes']}
        attrkeys = set(attrdict.keys())

        self.assertEqual({'article', 'plural', 'definition'}, attrkeys)
        self.assertEqual("der", attrdict['article'])
        self.assertEqual("Xxxxxxxxxx", attrdict['plural'])
        self.assertEqual("feelthy", attrdict['definition'])

        # add again but with empty attribute list

        add_attr_payload = {
            "attributes": [
            ]
        }

        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, word_id), json=add_attr_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(3, len(obj['attributes']))

        attrdict = {r['attrkey']: r['attrvalue'] for r in obj['attributes']}
        attrkeys = set(attrdict.keys())

        self.assertEqual({'article', 'plural', 'definition'}, attrkeys)
        self.assertEqual("der", attrdict['article'])
        self.assertEqual("Xxxxxxxxxx", attrdict['plural'])
        self.assertEqual("feelthy", attrdict['definition'])

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

    # adding the same word twice is ok, should have different word ids.
    def test_add_twice(self):
        add_payload = {
            "word": "test_add_twice",
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
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id_1 = obj['word_id']

        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id_2 = obj['word_id']

        self.assertNotEqual(word_id_1, word_id_2)

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_1))
        self.assertEqual(r.status_code, 200)

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_2))
        self.assertEqual(r.status_code, 200)

    # update payload with empty attribute list and no word - this is ok and should do nothing.
    def test_put_nothing(self):
        add_payload = {
            "word": "test_put_nothing",
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
        r = requests.post(config.Config.BASE_URL + "/api/word", json=add_payload)
        obj = r.json()
        word_id = obj['word_id']

        update_payload = {
            'attributes': []
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        obj = r.json()

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)


class APITestsAttributePOST(unittest.TestCase):
    # tests
    # bullshit word id
    def test_bullshit_word_id(self):
        payload = {
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
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, 66666666), data=payload)
        self.assertNotEqual(r.status_code, 200)

    # attributes keyword missing
    def test_attributes_keyword_missing(self):
        payload = {
        }
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, 66666666), data=payload)
        self.assertNotEqual(r.status_code, 200)

    # attrkey keyword missing
    def test_attrkey_keyword_missing(self):
        payload = {
            "attributes": [
                {
                    "attrvalue": "der"
                }
            ]
        }
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, 66666666), data=payload)
        self.assertNotEqual(r.status_code, 200)

    # attrvalue keyword missing
    def test_attrvalue_keyword_missing(self):
        payload = {
            "attributes": [
                {
                    "attrkey": "definition"
                }
            ]
        }
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, 66666666), data=payload)
        self.assertNotEqual(r.status_code, 200)

    # payload not JSON
    def test_payload_not_json(self):
        payload = "bullshit payload"
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, 66666666), data=payload)
        self.assertNotEqual(r.status_code, 200)

    # attrkeys wrong for word/pos
    def test_wrong_attrkeys(self):
        payload = {
            "attributes": [
                {
                    "attrkey": "euioeuioeu",
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
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, 66666666), data=payload)
        self.assertNotEqual(r.status_code, 200)

    # zero-length attribute values
    def test_empty_attrvalue(self):
        payload = {
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": ""
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
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, 66666666), data=payload)
        self.assertNotEqual(r.status_code, 200)

    # TODO: empty attribute list is ok.


class APITests(unittest.TestCase):
    def test_real_list_attribute_data(self):
        url = "%s/api/list_attributes/%s" % (config.Config.DB_URL, 126)
        r = requests.get(url)
        result = json.loads(r.text)
        jsonschema.validate(result, dlernen_json_schema.WORDLIST_ATTRIBUTE_SCHEMA)

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

    def test_real_wordlist(self):
        r = requests.get(config.Config.BASE_URL + "/api/wordlists")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDLISTS_SCHEMA)

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
