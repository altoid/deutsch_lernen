import unittest
import jsonschema
from dlernen import dlernen_json_schema

# none of the tests here uses the API or hits the database.  these tests make sure that the JSONSCHEMA documents
# are defined correctly.


class Test_COPY_AND_PASTE_TO_CREATE_SCHEMA_TEST_CLASS(unittest.TestCase):
    schema = dlernen_json_schema.NULL_SCHEMA

    valid_docs = [
    ]

    invalid_docs = [
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_REFRESH_WORDLISTS_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.REFRESH_WORDLISTS_PAYLOAD_SCHEMA

    valid_docs = [
        {
            "word": "oaeuhntoaeu"
        }
    ]

    invalid_docs = [
        {},
        {
            "word": None
        },
        {
            "word": ""
        },
        {
            "word": " "
        }
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_POS_STRUCTURE_RESPONSE_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.POS_STRUCTURE_RESPONSE_SCHEMA

    valid_docs = [
        [
            # 1 or more of these
            {
                # required
                "pos_name": "Verb",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,

                # required but can be empty
                "attributes": [
                    {
                        # all of these are required
                        "attrkey": "definition",
                        "attribute_id": 1234,
                        "sort_order": 5,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    },
                    {
                        "attrkey": "first_person_singular",
                        "attribute_id": 1234,
                        "sort_order": 6,
                        "attrvalue": None,
                        "attrvalue_id": None,
                    }
                ]
            },
            {
                "pos_name": "Conjunction",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "definition",
                        "attribute_id": 1234,
                        "sort_order": 0,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": None,
                "word_id": None,
                "attributes": [
                    {
                        "attrkey": "definition",
                        "attribute_id": 1234,
                        "sort_order": 0,
                        "attrvalue": None,
                        "attrvalue_id": None,
                    }
                ]
            }
        ]
    ]

    invalid_docs = [
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [],  # can't be empty
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "whatevs",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "id cannot be null if there is a value",
                        "attrvalue_id": None,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "whatevs",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": None,  # if this is null, attrvalue_id must be null too.
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        # "attrkey": "whatevs",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "whatevs",
                        # "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "whatevs",
                        "attribute_id": 1234,
                        # "sort_order": 11,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "whatevs",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        # "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "whatevs",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "aoeu",
                        # "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            # empty is bad.  it means there are no parts of speech in the database!
        ],
        [
            {
                "pos_name": "no_attributes",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                # "attributes": [
                #     {
                #         "attrkey": "whatevs",
                #         "attribute_id": 1234,
                #         "sort_order": 11,
                #         "attrvalue": "aoeu",
                #         "attrvalue_id": 1234,
                #     }
                # ]
            }
        ],
        [
            {
                # "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "missing_pos",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                # "pos_id": 1234,
                "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "missing_pos",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                # "word": "aoeu",
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "missing_pos",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                # "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "missing_pos",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "aoeu",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": "aoeu",
                "word_id": None,
                "attributes": [
                    {
                        "attrkey": "missing_pos",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "word and word id must be both null or not null",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": None,
                "word_id": 1234,
                "attributes": [
                    {
                        "attrkey": "missing_pos",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "word and word id must be both null or not null",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
        [
            {
                "pos_name": "voib",
                "pos_id": 1234,
                "word": None,
                "word_id": None,
                "attributes": [
                    {
                        "attrkey": "missing_pos",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "if word info is null then there should be nulls for attrs too",
                        "attrvalue_id": 1234,
                    }
                ]
            }
        ],
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_RESPONSE_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.WORDLIST_RESPONSE_SCHEMA

    valid_docs = [
        {'citation': None,
         'known_words': [{'article': None,
                          'definition': "it's an adjective",
                          'word': 'anohteduntaheoud',
                          'word_id': 9185},
                         {'article': None,
                          'definition': "no it's a floor cleaner",
                          'word': 'anohteduntaheoud',
                          'word_id': 9186},
                         {'article': None,
                          'definition': "now it's a noun",
                          'word': 'Anohteduntaheoud',
                          'word_id': 9187},
                         {'article': None,
                          'definition': None,  # null is OK
                          'word': 'anohteduntaheoud',
                          'word_id': 9188},
                         {'article': None,
                          'definition': "look it's a verb",
                          'word': 'anohteduntaheoud',
                          'word_id': 9189}],
         'list_type': 'standard',
         'name': 'aaa fake list 1',
         'notes': None,
         'source_is_url': False,
         'sqlcode': None,
         'unknown_words': [],
         'wordlist_id': 4237},
        {
            "name": "sample_word_list",
            "wordlist_id": 1234,
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
        },
        {
            "name": "no words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "null citation and notes",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            "citation": None,
            "source_is_url": False,
            "unknown_words": [],
            "notes": None
        }
    ]

    invalid_docs = [
        {
            "name": "bad dog",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [
                "whitespace not allowed"
            ],
            "notes": "lots of stuff"
        },
        {
            "name": "whitespace in word",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [
                {
                    "word": "whitespace in word",
                    "word_id": 1234,
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "missing word id",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [
                {
                    "word": "missing_word_id"
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "bullshit list type",
            "wordlist_id": 1234,
            "list_type": "bullshit",
            "known_words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            # "name": "no words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            # "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 1234,
            # "list_type": "standard",
            "known_words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            # "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            "citation": "where i got this",
            # "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            "citation": "where i got this",
            "source_is_url": False,
            # "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            # "notes": "lots of stuff"
        },
        {
            # empty doc not allowed
        }
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLISTS_RESPONSE_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.WORDLISTS_RESPONSE_SCHEMA

    valid_docs = [
        [
            {
                "name": "sample_word_list",
                "wordlist_id": 1234,
                "count": 111,
                "list_type": "standard"
            }
        ]
    ]

    invalid_docs = [
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_QUIZ_DATA_RESPONSE_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.QUIZ_DATA_RESPONSE_SCHEMA

    valid_docs = [
        [
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
    ]

    invalid_docs = [
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORD_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.WORD_PAYLOAD_SCHEMA

    valid_docs = [
        {
            # empty payload is allowed
        },
        {
            # fully specified payload
            "word": "werd",
            "pos_id": 1234,
            "attributes_adding": [
                {
                    "attrkey": "key",
                    "attrvalue": "value"
                }
            ],
            "attributes_deleting": [
                12,
                34,
                56
            ],
            "attributes_updating": [
                {
                    "attrvalue_id": 123,
                    "attrvalue": "new value"
                }
            ]
        },
        {
            # without any attribute values is valid
            "word": "valid"
        },
        {
            "attributes_adding": [],
            "attributes_deleting": [],
            "attributes_updating": []
        }
    ]

    invalid_docs = [
        {
            "attributes_adding": [
                {
                    "attrkey": "  noWhitespaceInKey",
                    "attrvalue": "aoeu"
                }
            ]
        },
        {
            "attributes_adding": [
                {
                    "attrkey": "key",
                    "attrvalue": " "  # must have at least 1 non-whitespace character
                }
            ]
        },
        {
            "attributes_adding": [
                {
                    "attrkey": "keyAndValueBothRequired"
                }
            ]
        },
        {
            "attributes_adding": [
                {
                    "attrvalue": "keyAndValueBothRequired"
                }
            ]
        },
        {
            "attributes_updating": [
                {
                    "attrvalue_id": 1234,
                    "attrvalue": "   "  # must have at least 1 non-whitespace character
                }
            ]
        },
        {
            "attributes_updating": [
                {
                    # id and value both required
                    "attrvalue_id": 1234
                }
            ]
        },
        {
            "attributes_updating": [
                {
                    "attrvalue": "id and value both required"
                }
            ]
        },
        {
            "attributes_deleting": [
                "has to be", "a list of ints"
            ]
        },
        {
            "word": ""
        },
        {
            "word": " "
        },
        {
            "word": "cannot have whitespace"
        }
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDS_RESPONSE_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.WORDS_RESPONSE_SCHEMA

    valid_docs = [
        [
            {
                "attributes": [
                    {'attrkey': 'definition',
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
                     'attrvalue': 'verdorben'}
                ],
                "pos_name": "Verb",
                "word": "verderben",
                "word_id": 2267
            }
        ]
    ]

    invalid_docs = [
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_CONTENTS_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.WORDLIST_CONTENTS_PAYLOAD_SCHEMA

    valid_docs = [
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

    invalid_docs = [
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
            "words": [
                "unknown words should not have spaces."
            ]
        },
        {
            "words": "value should be an array"
        }
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_METADATA_PAYLOAD_SCHEMA(unittest.TestCase):
    # note:  these tests don't validate sqlcode.  that happens in the API tests.

    schema = dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA

    valid_docs = [
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

    invalid_docs = [
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

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_METADATA_RESPONSE_SCHEMA(unittest.TestCase):
    schema = dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA

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

    def test_valid_docs(self):
        for jdoc in self.valid_responses:
            with self.subTest(jdoc=jdoc):
                jsonschema.validate(jdoc, self.schema)

    def test_invalid_docs(self):
        for jdoc in self.invalid_responses:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    jsonschema.validate(jdoc, self.schema)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)
