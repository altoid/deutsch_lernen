import unittest
import jsonschema
from dlernen import dlernen_json_schema

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

SAMPLE_POS_STRUCTURE_RESPONSE = [
    # 0 or more of these
    {
        # required
        "name": "Verb",

        # required but can be empty
        "attributes": [
            {
                # both of these are required
                "attrkey": "definition",
                "sort_order": 5,
            },
            {
                "attrkey": "first_person_singular",
                "sort_order": 6
            }
        ]
    },
    {
        "name": "Conjunction",
        "attributes": [
            {
                "attrkey": "definition",
                "sort_order": 0
            }
        ]
    }
]

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
        'attributes': {
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
    }
]

SAMPLE_WORDLIST_RESPONSE = {
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


class CheckDocumentDefinitions(unittest.TestCase):
    """
    run check_schema on all the document types.
    """

    all_the_docs = [
        dlernen_json_schema.ADDATTRIBUTES_PAYLOAD_SCHEMA,
        dlernen_json_schema.ADDWORD_PAYLOAD_SCHEMA,
        dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA,
        dlernen_json_schema.QUIZ_DATA_RESPONSE_SCHEMA,
        dlernen_json_schema.REFRESH_WORDLISTS_PAYLOAD_SCHEMA,
        dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA,
        dlernen_json_schema.WORD_METADATA_RESPONSE_SCHEMA,
        dlernen_json_schema.WORDLIST_CONTENTS_PAYLOAD_SCHEMA,
        dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA,
        dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA,
        dlernen_json_schema.WORDLIST_RESPONSE_SCHEMA,
        dlernen_json_schema.WORDLISTS_RESPONSE_SCHEMA,
        dlernen_json_schema.WORDS_RESPONSE_SCHEMA,
    ]

    def test_check_schema_docs(self):
        for jdoc in self.all_the_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.Draft202012Validator.check_schema(jdoc)


class SchemaTests(unittest.TestCase):
    def test_pos_structure_response_sample_1(self):
        jsonschema.validate(SAMPLE_POS_STRUCTURE_RESPONSE, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

    def test_pos_structure_response_sample_2(self):
        doc = [
        ]

        jsonschema.validate(doc, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

    def test_pos_structure_response_sample_3(self):
        doc = [
            {
                "name": "voib",
                "attributes": []  # can't be empty
            }
        ]

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(doc, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

    def test_pos_structure_response_sample_4(self):
        doc = [
            {
                "name": "voib",
                "attributes": [
                    {
                        "attrkey": "definition",
                        "sort_order": 0,
                    }
                ]
            }
        ]

        jsonschema.validate(doc, dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA)

    def test_word_sample(self):
        jsonschema.validate(SAMPLE_WORDS_RESULT, dlernen_json_schema.WORDS_RESPONSE_SCHEMA)

    def test_addword_payload_sample(self):
        jsonschema.validate(SAMPLE_ADDWORD_PAYLOAD, dlernen_json_schema.ADDWORD_PAYLOAD_SCHEMA)

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

    def test_add_attributes_payload_sample(self):
        jsonschema.validate(SAMPLE_ADDATTRIBUTES_PAYLOAD, dlernen_json_schema.ADDATTRIBUTES_PAYLOAD_SCHEMA)

    def test_quiz_data_sample(self):
        jsonschema.validate(SAMPLE_QUIZ_DATA_RESULT, dlernen_json_schema.QUIZ_DATA_RESPONSE_SCHEMA)

    def test_wordlists_sample(self):
        jsonschema.validate(SAMPLE_WORDLISTS_RESULT, dlernen_json_schema.WORDLISTS_RESPONSE_SCHEMA)

    def test_wordlist_response_sample(self):
        jsonschema.validate(SAMPLE_WORDLIST_RESPONSE, dlernen_json_schema.WORDLIST_RESPONSE_SCHEMA)


class WordlistContentsPayload(unittest.TestCase):
    valid_payloads = [
        {
        },
        {
            "notes": None
        },
        {
            "notes": "whatevs"
        },
        {
            "words": []
        },
        {
            "words": [
                "aoeu",
                "nthdue",
                "eoathudt"
            ]
        },
        {
            "notes": "whatevs",
            "words": [
                "aoeu",
                "ioeuioeu"
            ]
        }
    ]

    invalid_payloads = [
        {
            "words": [
                ""
            ]
        },
        {
            "words": [
                "  "
            ]
        },
        {
            "words": "value should be an array"
        }
    ]

    def test_valid_payloads(self):
        for jdoc in self.valid_payloads:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, dlernen_json_schema.WORDLIST_CONTENTS_PAYLOAD_SCHEMA)

    def test_invalid_payloads(self):
        for jdoc in self.invalid_payloads:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, dlernen_json_schema.WORDLIST_CONTENTS_PAYLOAD_SCHEMA)


class WordUpdatePayload(unittest.TestCase):
    valid_payloads = [
        {
        }
    ]

    invalid_payloads = [
    ]

    def test_valid_payloads(self):
        for jdoc in self.valid_payloads:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)

    def test_invalid_payloads(self):
        for jdoc in self.invalid_payloads:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, dlernen_json_schema.UPDATEWORD_PAYLOAD_SCHEMA)


class WordlistMetadataPayload(unittest.TestCase):
    # note:  these tests don't validate sqlcode.  that happens in the API tests.

    valid_payloads = [
        {
            "name": "saetuasasue",
            "citation": "anteohusntaeo",
            "sqlcode": "n;sercisr;cih"
        },
        {
            "name": "saetuasasue",
            "citation": None,
            "sqlcode": None
        },
        {
            "name": "x"
        },
        {
            "citation": "    xxx    "
        },
        {
            "sqlcode": "  line1\r\nline2\r\nline3  "
        },
        {
            # empty payloads are valid
        }
    ]

    invalid_payloads = [
        {
            "name": "  leading and trailing whitespace not allowed  "
        },
        {
            "name": None
        },
        {
            "sqlcode": ""
        },
        {
            "citation": ""
        }
    ]

    def test_valid_payloads(self):
        for jdoc in self.valid_payloads:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)

    def test_invalid_payloads(self):
        for jdoc in self.invalid_payloads:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)


class WordlistMetadataResponse(unittest.TestCase):
    valid_responses = [
        {
            "wordlist_id": 1234,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "  speeding  ",
            "list_type": "empty"
        },
        {
            "wordlist_id": 1234,
            "name": "fester",
            "sqlcode": None,
            "citation": None,
            "list_type": "empty"
        }
    ]

    invalid_responses = [
        # any required fields not present should cause validation error
        {
            # "wordlist_id": 1234,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty"
        },
        {
            "wordlist_id": 1234,
            # "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty"
        },
        {
            "wordlist_id": 1234,
            "name": "fester",
            # "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty"
        },
        {
            "wordlist_id": 1234,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            # "citation": "speeding",
            "list_type": "empty"
        },
        {
            "wordlist_id": 1234,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding"
            # "list_type": "empty",
        },
        {
            # bad list type
            "wordlist_id": 1234,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "  speeding  ",
            "list_type": "shopping"
        },
        {
            # bad name
            "wordlist_id": 1234,
            "name": "   fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty"
        },
        {
            # another bad name
            "wordlist_id": 1234,
            "name": "",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty"
        },
        {
            # bad sqlcode
            "wordlist_id": 1234,
            "name": "aoeu",
            "sqlcode": "",
            "citation": "speeding",
            "list_type": "empty"
        },
        {
            # bad citation
            "wordlist_id": 1234,
            "name": "aoeu",
            "sqlcode": "not really sql but what the hell",
            "citation": "",
            "list_type": "empty"
        },
        {
            # bad id
            "wordlist_id": "1234",
            "name": "aoeu",
            "sqlcode": "not really sql but what the hell",
            "citation": "aoeuoea",
            "list_type": "empty"
        },
        {

        }
    ]

    def test_valid_payloads(self):
        for jdoc in self.valid_responses:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)

    def test_invalid_payloads(self):
        for jdoc in self.invalid_responses:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)
