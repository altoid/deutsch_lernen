import unittest
import jsonschema
import requests
from dlernen import dlernen_json_schema, config
import json
from pprint import pprint
import random
import string

SAMPLE_WORDLIST_PAYLOAD = {
    "name": "saetuasasue",
    "citationsource": "anteohusntaeo",
    "sqlcode": "n;sercisr;cih",
    "notes": "aoeuaoeu",
    "words": [
        "bla",
        "bazz",
        "whee"
    ]
}

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
    # the attributes lists are optional and can be empty.  if not empty they must have the right structure.
    "attributes_updating": [
        {
            "attrvalue_id": 444,
            "attrvalue": "der"  # cannot be empty string.
        },
        {
            "attrvalue_id": 555,
            "attrvalue": "Foofoo"
        }
    ],
    "attributes_deleting": [
        444,
        555
    ],
    "attributes_adding": [
        {
            "attrkey": "article",
            "attrvalue": "der"  # cannot be empty string.
        },
        {
            "attrkey": "definition",
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
    "attribute_id": 1234,
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

SAMPLE_WORDLIST_METADATA_RESULT = {
    "sqlcode": "select distinct word_id\r\nfrom mashup_v\r\nwhere pos_name = 'verb'\r\nand word like '%gehe%'",
    "wordlist_id": 126,
    "name": "verbs like *geh*",
    "citation": ""
}

SAMPLE_WORDLISTS_RESULT = [
    {
        "name": "sample_word_list",
        "wordlist_id": 1234,
        "count": 111,
        "list_type": "standard"
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
    "list_type": "standard",
    "known_words": [
        {
            "word": "aoeuaeou",
            "word_id": 123,
            "definition": "hell if i know"
        },
        {
            "word": "Iethdsenihtd",
            "word_id": 465,
            "article": "das",
            "definition": "an odd noun"
        }
    ],
    "citation": "where i got this",
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

    def test_wordlist_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDLIST_PAYLOAD_SCHEMA)

    def test_wordlist_payload_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_PAYLOAD, dlernen_json_schema.WORDLIST_PAYLOAD_SCHEMA)

    def test_wordlist_empty_payload(self):
        jsonschema.validate({}, dlernen_json_schema.WORDLIST_PAYLOAD_SCHEMA)

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

    def test_updateword_payload_sample_2(self):
        sample_payload = {}
        jsonschema.validate(sample_payload, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_updateword_payload_sample_3(self):
        sample_payload = {
            'word': 'wordonly'
        }
        jsonschema.validate(sample_payload, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_updateword_payload_sample_4(self):
        sample_payload = {
            'attributes_adding': [],
            'attributes_deleting': [],
            'attributes_updating': []
        }
        jsonschema.validate(sample_payload, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_updateword_payload_sample_5(self):
        sample_payload = {
            'attributes_adding': [
                {
                    "attrkey": "no value"
                }
            ]
        }

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(sample_payload, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_updateword_payload_sample_6(self):
        sample_payload = {
            'attributes_updating': [
                {
                    "attrvalue": "no id"
                }
            ]
        }

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(sample_payload, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_add_attributes_payload_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.ADDATTRIBUTES_PAYLOAD_SCHEMA)

    def test_add_attributes_payload_sample(self):
        jsonschema.validate(SAMPLE_ADDATTRIBUTES_PAYLOAD, dlernen_json_schema.ADDATTRIBUTES_PAYLOAD_SCHEMA)

    def test_list_attribute_schema(self):
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDLIST_METADATA_SCHEMA)

    def test_list_attribute_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_METADATA_RESULT, dlernen_json_schema.WORDLIST_METADATA_SCHEMA)

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
        jsonschema.Draft202012Validator.check_schema(dlernen_json_schema.WORDLIST_SCHEMA)

    def test_wordlist_detail_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_DETAIL_RESULT, dlernen_json_schema.WORDLIST_SCHEMA)


class APITestsWordPOST(unittest.TestCase):
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
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
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
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
        self.assertNotEqual(r.status_code, 200)

    # payload not json
    def test_payload_not_json(self):
        payload = "this is some bullshit right here"
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
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
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
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
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
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
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
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
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
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
        r = requests.post(config.Config.BASE_URL + "/api/word", json=payload)
        self.assertNotEqual(r.status_code, 200)


class APITestsWordPUT(unittest.TestCase):
    def setUp(self):
        self.word = "APITestsWordPut"
        add_payload = {
            "word": self.word,
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
        self.obj = r.json()
        self.word_id = self.obj['word_id']

    def tearDown(self):
        requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))

    # bullshit word id
    def test_bullshit_word_id(self):
        update_payload = {
            "word": "blah",
            "attributes_updating": [
                {
                    "attrvalue_id": self.obj['attributes'][0]['attrvalue_id'],
                    "attrvalue": "der"
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, 5555555555), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # bullshit attr ids
    def test_update_bullshit_attrids(self):
        update_payload = {
            "word": "blah",
            "attributes_updating": [
                {
                    "attrvalue_id": 5555555555555,
                    "attrvalue": "der"
                },
                {
                    "attrvalue_id": 666666666666666,
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    def test_delete_bullshit_attrids(self):
        update_payload = {
            "word": "blah",
            "attributes_deleting": [
                555555555555555,
                666666666666666
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # zero-length word
    def test_zero_length_word(self):
        # updating with word = "" not allowed.
        update_payload = {
            "word": "",
            "attributes_updating": [
                {
                    "attrvalue_id": self.obj['attributes'][0]['attrvalue_id'],
                    "attrvalue": "der"
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # zero-length attribute value
    def test_zero_length_attrvalue(self):
        # updating with attrvalue = "" not allowed.
        update_payload = {
            "word": "aoeuoae",
            "attributes_updating": [
                {
                    "attrvalue_id": self.obj['attributes'][0]['attrvalue_id'],
                    "attrvalue": ""
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # attrvalue keyword missing
    def test_attrvalue_keyword_missing(self):
        update_payload = {
            "word": "aoeuoae",
            "attributes_updating": [
                {
                    "attrvalue_id": self.obj['attributes'][0]['attrvalue_id']
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # attrvalue_id keyword missing
    def test_attrvalue_id_keyword_missing(self):
        update_payload = {
            "word": "aoeuoae",
            "attributes_updating": [
                {
                    "attrvalue": "turnips"
                },
                {
                    "attrvalue_id": self.obj['attributes'][1]['attrvalue_id'],
                    "attrvalue": "Foofoo"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # payload not json
    def test_payload_not_json(self):
        update_payload = "serious bullshit right here"

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertNotEqual(200, r.status_code)

    # changing the spelling of a word works.
    def test_change_spelling(self):
        new_word = 'aoeuaeouoeau'
        update_payload = {
            'word': new_word
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        obj = r.json()
        self.assertEqual(new_word, obj['word'])

    # updating attribute values works.
    def test_update_attrs(self):
        victim = self.obj['attributes'][0]['attrvalue_id']
        new_value = 'changed to this'
        new_word = 'respell_word_succeeded'
        update_payload = {
            'word': new_word,
            'attributes_updating': [
                {
                    'attrvalue_id': victim,
                    'attrvalue': new_value
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(new_word, obj['word'])
        a = list(filter(lambda x: x['attrvalue_id'] == victim, obj['attributes']))
        self.assertEqual(1, len(a))
        self.assertEqual(new_value, a[0]['attrvalue'])

    # trivial no-op payload is ok.
    def test_noop_update(self):
        update_payload = {
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=update_payload)
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        obj = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(3, len(obj['attributes']))
        self.assertEqual(self.word, obj['word'])

    # other tests from end-to-end might be appropriate here.


# TODO:  make sure proper cleanup happens if any assertions fail on status code values.  setup/teardown?


class APITestsWordEndToEnd(unittest.TestCase):
    # end-to-end test:  add a word, verify existence, delete it, verify deletion.
    # delete it again, should be no errors.

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

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word_id))
        self.assertEqual(404, r.status_code)

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
        word = "test_add_twice_%s" % ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            "word": word,
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

        # get word by name
        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, word))
        obj = r.json()
        self.assertEqual(2, len(obj))

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_1))
        self.assertEqual(r.status_code, 200)

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_2))
        self.assertEqual(r.status_code, 200)


class APITestsAttributePOST(unittest.TestCase):
    def setUp(self):
        add_payload = {
            "word": "APITestsAttributePOST",
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
        obj = r.json()
        self.word_id = obj['word_id']

    def tearDown(self):
        requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))

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
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, 66666666), json=payload)
        self.assertNotEqual(r.status_code, 200)

    # attributes keyword missing
    def test_attributes_keyword_missing(self):
        payload = {
        }
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, self.word_id), json=payload)
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
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, self.word_id), json=payload)
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
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertNotEqual(r.status_code, 200)

    # payload not JSON
    def test_payload_not_json(self):
        payload = "bullshit payload"
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, self.word_id), json=payload)
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
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, self.word_id), json=payload)
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
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertNotEqual(r.status_code, 200)

    def test_adding_more_values(self):
        # test that adding additional attribute values is well-behaved

        payload = {
            "attributes": [
                {
                    "attrkey": "article",
                    "attrvalue": "dee"
                },
                {
                    "attrkey": "plural",
                    "attrvalue": "Xxxxxxxxxx_another"
                },
                {
                    "attrkey": "definition",
                    "attrvalue": "feelthier"
                }
            ]
        }
        r = requests.post("%s/api/%s/attribute" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        obj = r.json()
        self.assertEqual(6, len(obj['attributes']))

        test_dict = {}
        for a in obj['attributes']:
            if a['attrkey'] not in test_dict:
                test_dict[a['attrkey']] = set()
            test_dict[a['attrkey']].add(a['attrvalue'])

        self.assertEqual({'der', 'dee'}, test_dict['article'])
        self.assertEqual({'Xxxxxxxxxx', 'Xxxxxxxxxx_another'}, test_dict['plural'])
        self.assertEqual({'feelthy', 'feelthier'}, test_dict['definition'])


class APITests(unittest.TestCase):
    def test_real_quiz_data(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quiz_key": "plurals",
            "word_ids": [2175, 3230, 4803]
        }
        r = requests.put(url, json=payload)
        quiz_data = r.json()
        jsonschema.validate(quiz_data, dlernen_json_schema.QUIZ_DATA_SCHEMA)

    def test_empty_quiz_data(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quiz_key": "plurals",
            "word_ids": []
        }
        r = requests.put(url, json=payload)
        quiz_data = r.json()
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

    def test_get_word_no_match(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/anehuintaoedhunateohdu")
        self.assertEqual(404, r.status_code)

    def test_get_word_by_word_partial(self):
        r = requests.get(config.Config.BASE_URL + "/api/word/geh?partial=true")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDS_SCHEMA)

    def test_quiz_data_empty_list_1(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quiz_key": "definitions"
        }

        r = requests.put(url, json=payload)
        result = json.loads(r.text)
        self.assertEqual([], result)

    def test_quiz_data_empty_list_2(self):
        url = "%s/api/quiz_data" % config.Config.DB_URL
        payload = {
            "quiz_key": "definitions",
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
        url = "%s&wordlist_id=%s" % (url, ','.join(args))

        r = requests.get(url)
        self.assertEqual(200, r.status_code)
        payload = r.json()

        url = "%s/api/words" % config.Config.DB_URL
        r = requests.put(url, json=payload)
        results = json.loads(r.text)
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDS_SCHEMA)


class APIWordlists(unittest.TestCase):
    # get all wordlists
    def test_real_wordlist(self):
        r = requests.get(config.Config.BASE_URL + "/api/wordlists")
        results = r.json()
        self.assertGreater(len(results), 0)
        jsonschema.validate(results, dlernen_json_schema.WORDLISTS_SCHEMA)


class APIWordlist(unittest.TestCase):
    # add list with no words, just a name
    def test_create_empty_list(self):
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        # do a GET - known and unknown lists should be empty
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual("empty", obj['list_type'])
        
        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

        # do a GET - should be gone
        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 404)

    # add list with everything, incl. known and unknown words
    def test_create_dumb_list(self):
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'words': [
                'werfen', # known
                'natehdnaoehu' # unknown, hopefully
            ],
            'notes': 'important notes',
            'citation': 'confidential'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # add smart list with everything
    def test_create_smart_list(self):
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'notes': 'important notes',
            'source': 'confidential',
            'sqlcode': 'select id word_id from word where id = 124'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual("smart", obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # update list
    def test_update_list(self):
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'name': list_name + "__RENAMED",
            'notes': 'notes here',
            'sqlcode': 'select id word_id from word where id = 100',
            'citation': 'some article'
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        for k in update_payload.keys():
            self.assertEqual(update_payload[k], obj[k])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # add word to list
    def test_add_words_to_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        gibberish = 'aoeunhatedu'
        add_payload = {
            'name': list_name,
            'words': [
                'werfen',
                'geben',
                gibberish
            ]
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'words': [
                'wecken',
                'werfen',  # already there, should be a noop
                'nachgebend',
                gibberish
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        known_words = {x['word'] for x in obj['known_words']}
        unknown_words = {x for x in obj['unknown_words']}

        self.assertEqual({'wecken', 'nachgebend', 'geben', 'werfen'}, known_words)
        self.assertEqual({gibberish}, unknown_words)

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # update list with empty payload --> noop
    def test_update_list_empty_payload(self):
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': """select id word_id from word where word = 'geben'"""
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        wordlist_id = obj['wordlist_id']

        update_payload = {
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, wordlist_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        for k in add_payload.keys():
            self.assertEqual(add_payload[k], obj[k])

        self.assertTrue(len(obj['known_words']) > 0)

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, wordlist_id))
        self.assertEqual(r.status_code, 200)

    # remove word by word from list -> removes from unknown
    def test_remove_word_by_word(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        payload = {
            'name': list_name,
            'words': [
                'werfen',  # known
                gibberish  # unknown, hopefully
            ],
            'notes': 'important notes',
            'citation': 'confidential'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertTrue(len(obj['unknown_words']) > 0)
        word = obj['unknown_words'][0]
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, list_id, word))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(1, len(obj['known_words']))
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # remove word by id from list
    def test_remove_word_by_id(self):
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'words': [
                'werfen', # known
                'natehdnaoehu' # unknown, hopefully
            ],
            'notes': 'important notes',
            'citation': 'confidential'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertTrue(len(obj['known_words']) > 0)
        word_id = obj['known_words'][0]['word_id']
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, list_id, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(0, len(obj['known_words']))
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual('standard', obj['list_type'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    def test_update_smart_list(self):
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'notes': 'important notes',
            'citation': 'confidential',
            'sqlcode': 'select id word_id from word where id = 124'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        new_code = 'select id word_id from word where id = 666'
        new_name = "%s%s" % (list_name, '__UPDATED')
        new_citation = 'really confidential'
        payload = {
            'name': new_name,
            'citation': new_citation,
            'sqlcode': new_code
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        r = requests.get("%s/api/wordlist/%s/metadata" % (config.Config.BASE_URL, list_id), json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(new_code, obj['sqlcode'])
        self.assertEqual(new_citation, obj['citation'])
        self.assertEqual(new_name, obj['name'])

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # add list with existing name
    def test_add_existing_name(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        list_id = obj['wordlist_id']

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 500)

        # delete it
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        self.assertEqual(r.status_code, 200)

    # add list with empty name
    def test_add_empty_name(self):
        list_name = " "
        payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 400)

    # add list with empty payload
    def test_add_empty_payload(self):
        payload = {
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 400)

    # update list with empty name
    def test_update_with_empty_name(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))

        # don't allow create or update with empty name

        # create a word list

        create_url = "%s/api/wordlist" % config.Config.DB_URL
        payload = {
            'name': ''
        }
        r = requests.post(create_url, json=payload)
        self.assertEqual(400, r.status_code)

        payload = {
            'name': list_name
        }
        r = requests.post(create_url, json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        # set list name to empty string - should be error

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        payload = {
            'name': ''
        }
        r = requests.put(url, json=payload)
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

    # add list with code and words --> only one is allowed.
    def test_add_list_with_code_and_words(self):
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 666',
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=payload)
        self.assertEqual(r.status_code, 400)

    # add code to dumb list --> not allowed if list has words, ok if empty
    def test_add_code_to_dumb_list(self):
        # not allowed
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(400, r.status_code)

        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, list_id)
        r = requests.delete(url)
        self.assertEqual(200, r.status_code)

    # add words to smart list --> not allowed.
    def test_add_words_to_smart_list(self):
        # not allowed
        list_name = "%s_%s" %(self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        update_payload = {
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(400, r.status_code)

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # get with bullshit wordlist id
    def test_get_bullshit_wordlist_id(self):
        url = "%s/api/wordlist/%s" % (config.Config.DB_URL, 6666666)
        r = requests.get(url)
        self.assertEqual(404, r.status_code)

    # tests for changing list type; many cases

    # change list type: create empty, change to standard
    def test_change_list_type_empty_to_standard(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('empty', obj['list_type'])

        update_payload = {
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('standard', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # change list type: create empty, change to smart
    def test_change_list_type_empty_to_smart(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('empty', obj['list_type'])

        update_payload = {
            'sqlcode': 'select id word_id from word where id = 111'
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('smart', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # change list type: create smart, change to empty
    def test_change_list_type_smart_to_empty(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('smart', obj['list_type'])

        update_payload = {
            'sqlcode': ''
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('empty', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # change list type: create smart, change to standard
    def test_change_list_type_smart_to_standard(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('smart', obj['list_type'])

        update_payload = {
            'sqlcode': '',
            'words': [
                'werfen',
                'aoeuaoeu'
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id), json=update_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.assertEqual('standard', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    # there is no test for create standard, change to smart
    # because this can't be done in one request.  we have to empty the list first
    # then change to smart.

    # change list type: create standard, change to empty
    def test_change_list_type_standard_to_empty(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        gibberish = ''.join(random.choices(string.ascii_lowercase, k=10))
        add_payload = {
            'name': list_name,
            'words': [
                'werfen',
                gibberish
            ]
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('standard', obj['list_type'])
        self.assertEqual(1, len(obj['unknown_words']))
        self.assertEqual(1, len(obj['known_words']))

        # remove the words one by one
        word = obj['unknown_words'][0]
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, list_id, word))
        self.assertEqual(r.status_code, 200)

        word_id = obj['known_words'][0]['word_id']
        r = requests.delete("%s/api/wordlist/%s/%s" % (config.Config.BASE_URL, list_id, word_id))
        self.assertEqual(r.status_code, 200)

        r = requests.get("%s/api/wordlist/%s" % (config.Config.BASE_URL, list_id))
        obj = r.json()

        self.assertEqual('empty', obj['list_type'])
        self.assertEqual(0, len(obj['unknown_words']))
        self.assertEqual(0, len(obj['known_words']))

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)

    def test_remove_words_from_smart_list(self):
        list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': list_name,
            'sqlcode': 'select id word_id from word where id = 555'
        }

        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        list_id = obj['wordlist_id']

        self.assertEqual('smart', obj['list_type'])

        r = requests.delete("%s/api/wordlist/%s/666" % (config.Config.BASE_URL, list_id))
        self.assertNotEqual(200, r.status_code)

        r = requests.delete("%s/api/wordlist/%s/teuhdunaoethu" % (config.Config.BASE_URL, list_id))
        self.assertNotEqual(200, r.status_code)

        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, list_id))
        self.assertEqual(200, r.status_code)


class APIWordUpdate(unittest.TestCase):
    def setUp(self):
        # create a random verb
        self.verb = ''.join(random.choices(string.ascii_lowercase, k=11))
        add_payload = {
            "word": self.verb,
            "pos_name": "verb"
        }

        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        obj = r.json()
        self.word_id = obj['word_id']

    def test_add_update_delete_attribute_1(self):
        # add, update, and delete the same attr value in 3 separate requests
        old_def = "it smells like cereal here"
        attrkey = "definition"
        payload = {
            "attributes_adding": [
                {
                    "attrkey": attrkey,
                    "attrvalue": old_def
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertEqual(old_def, defn['attrvalue'])

        # update definition
        new_def = "try this on for size"

        payload = {
            "attributes_updating": [
                {
                    "attrvalue_id": defn['attrvalue_id'],
                    "attrvalue": new_def
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertEqual(new_def, defn['attrvalue'])

        # delete
        payload = {
            "attributes_deleting": [
                defn['attrvalue_id']
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        attrs = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))
        defn = attrs[0]
        self.assertIsNone(defn['attrvalue'])

    def test_add_update_delete_attribute_2(self):
        # add, update, and delete attribute values in a single request
        old_def = "it smells like cereal here"
        payload = {
            "attributes_adding": [
                {
                    "attrkey": "definition",
                    "attrvalue": old_def
                },
                {
                    "attrkey": "first_person_singular",
                    "attrvalue": "mr_lonely"
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        # remove the definition, add 2nd person singular, update 1st person singular, in one request
        fps = list(filter(lambda x: x['attrkey'] == 'first_person_singular', obj['attributes']))[0]
        defn = list(filter(lambda x: x['attrkey'] == 'definition', obj['attributes']))[0]

        new_fps = "what hath god wrought"
        sps_val = "my nose hurts"
        payload = {
            "attributes_adding": [
                {
                    "attrkey": "second_person_singular",
                    "attrvalue": sps_val
                }
            ],
            "attributes_deleting": [
                defn['attrvalue_id']
            ],
            "attributes_updating": [
                {
                    "attrvalue_id": fps['attrvalue_id'],
                    "attrvalue": new_fps
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        fps = list(filter(lambda x: x['attrkey'] == 'first_person_singular', obj['attributes']))[0]
        sps = list(filter(lambda x: x['attrkey'] == 'second_person_singular', obj['attributes']))[0]
        defn = list(filter(lambda x: x['attrkey'] == 'definition', obj['attributes']))[0]

        self.assertEqual(new_fps, fps['attrvalue'])
        self.assertEqual(sps_val, sps['attrvalue'])
        self.assertIsNone(defn['attrvalue'])

    def test_update_delete_same_attr(self):
        # error if we attempt to update and delete the same attr id.
        old_def = "it smells like cereal here"
        attrkey = "definition"
        payload = {
            "attributes_adding": [
                {
                    "attrkey": attrkey,
                    "attrvalue": old_def
                }
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()

        defn = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))[0]

        payload = {
            "attributes_updating": [
                {
                    "attrvalue_id": defn['attrvalue_id'],
                    "attrvalue": "not the same at all"
                }
            ],
            "attributes_deleting": [
                defn['attrvalue_id']
            ]
        }

        r = requests.put("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id), json=payload)
        self.assertNotEqual(200, r.status_code)

        r = requests.get("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))
        self.assertEqual(200, r.status_code)
        obj = r.json()
        defn = list(filter(lambda x: x['attrkey'] == attrkey, obj['attributes']))[0]
        self.assertEqual(old_def, defn['attrvalue'])

    def tearDown(self):
        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, self.word_id))


class APIWordlistActions(unittest.TestCase):
    """
    tests of operations on lists where we need to set up and tear down a list.
    TODO: maybe some of the tests in APIWordlist can be moved here.
    """
    def setUp(self):
        self.list_name = "%s_%s" % (self.id(), ''.join(random.choices(string.ascii_lowercase, k=20)))
        add_payload = {
            'name': self.list_name
        }
        r = requests.post("%s/api/wordlist" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(200, r.status_code)
        obj = r.json()
        self.wordlist_id = obj['wordlist_id']

    def test_add_double_word(self):
        # add the same word twice to the dictionary
        # put both into the wordlist
        # make sure they both appear in the wordlist.
        random_noun = ''.join(random.choices(string.ascii_lowercase, k=20))
        add_payload = {
            "word": random_noun,
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

        # add the word to the dict again
        r = requests.post("%s/api/word" % config.Config.BASE_URL, json=add_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        word_id_2 = obj['word_id']

        update_payload = {
            'words': [
                random_noun
            ]
        }

        r = requests.put("%s/api/wordlist/%s" % (config.Config.BASE_URL, self.wordlist_id), json=update_payload)
        self.assertEqual(r.status_code, 200)
        obj = r.json()

        self.assertEqual(2, len(obj['known_words']))

        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_1))
        r = requests.delete("%s/api/word/%s" % (config.Config.BASE_URL, word_id_2))

    def tearDown(self):
        r = requests.delete("%s/api/wordlist/%s" % (config.Config.DB_URL, self.wordlist_id))
        self.assertEqual(200, r.status_code)


if __name__ == '__main__':
    unittest.main()
