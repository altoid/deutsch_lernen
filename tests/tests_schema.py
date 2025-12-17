import unittest
import jsonschema
from dlernen import dlernen_json_schema as js


# none of the tests here uses the API or hits the database.  these tests make sure that the JSONSCHEMA documents
# are defined correctly.


class Test_COPY_AND_PASTE_TO_CREATE_SCHEMA_TEST_CLASS(unittest.TestCase):
    schema = js.NULL_SCHEMA

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
    schema = js.REFRESH_WORDLISTS_PAYLOAD_SCHEMA

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
    schema = js.POS_STRUCTURE_RESPONSE_SCHEMA

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
                    },
                    {
                        "attrkey": "first_person_singular",
                        "attribute_id": 1234,
                        "sort_order": 6,
                        "attrvalue": None,
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
                        "attrvalue": "aoeu"
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
                        "attrvalue": None
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
                        # "attrkey": "whatevs",
                        "attribute_id": 1234,
                        "sort_order": 11,
                        "attrvalue": "aoeu"
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
                        "attrvalue": "aoeu"
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
                        "attrvalue": "aoeu"
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
                        # "attrvalue": "aoeu"
                    }
                ]
            }
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
                #         "attrvalue": "aoeu"
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
                        "attrvalue": "aoeu"
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
                        "attrvalue": "aoeu"
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
    schema = js.WORDLIST_RESPONSE_SCHEMA

    valid_docs = [
        {'citation': None,
         'known_words': [{'article': None,
                          'definition': "it's an adjective",
                          'word': 'anohteduntaheoud',
                          'tags': [],
                          'word_id': 9185},
                         {'article': None,
                          'definition': "no it's a floor cleaner",
                          'word': 'anohteduntaheoud',
                          'tags': ['abcd'],
                          'word_id': 9186},
                         {'article': None,
                          'definition': "now it's a noun",
                          'word': 'Anohteduntaheoud',
                          'tags': [],
                          'word_id': 9187},
                         {'article': None,
                          'definition': None,  # null is OK
                          'word': 'anohteduntaheoud',
                          'tags': [],
                          'word_id': 9188},
                         {'article': None,
                          'definition': "look it's a verb",
                          'word': 'anohteduntaheoud',
                          'tags': ['fish', 'heads'],
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
                    "tags": ["aoeu"],
                    "definition": "hell if i know"
                },
                {
                    "word": "Iethdsenihtd",
                    "word_id": 465,
                    "article": "das",
                    "tags": ["aoeu", "oeui"],
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
            "name": "messin with words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [
                {
                    # "word": "werrd",
                    "word_id": 1234,
                    "tags": ["egad"],
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "messin with words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [
                {
                    "word": "werrd",
                    # "word_id": 1234,
                    "tags": ["egad"],
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
        },
        {
            "name": "messin with words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "known_words": [
                {
                    "word": "werrd",
                    "word_id": 1234,
                    # "tags": ["egad"],
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "unknown_words": [],
            "notes": "lots of stuff"
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
    schema = js.WORDLISTS_RESPONSE_SCHEMA

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


class Test_QUIZ_ANSWER_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = js.QUIZ_ANSWER_PAYLOAD_SCHEMA

    valid_docs = [
        {
            'quiz_id': 123,
            'word_id': 123,
            'attribute_id': 123,
            'correct': True
        },
        {
            'quiz_id': 123,
            'word_id': 123,
            'attribute_id': 123,
            'correct': False
        },
    ]

    invalid_docs = [
        {
            # 'quiz_id': 123,
            'word_id': 123,
            'attribute_id': 123,
            'correctt': True,
        },
        {
            'quiz_id': 123,
            # 'word_id': 123,
            'attribute_id': 123,
            'correct': True,
        },
        {
            'quiz_id': 123,
            'word_id': 123,
            # 'attribute_id': 123,
            'correct': True,
        },
        {
            'quiz_id': 123,
            'word_id': 123,
            'attribute_id': 123,
            # 'correct': True,
        },
        {
            'quiz_id': 123,
            'word_id': 123,
            'attribute_id': 123,
            'correct': 0,  # wrong type
        },
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


class Test_QUIZ_REPORT_RESPONSE_SCHEMA(unittest.TestCase):
    schema = js.QUIZ_REPORT_RESPONSE_SCHEMA

    valid_docs = [
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [],
        },
    ]

    invalid_docs = [
        {
            # "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            # "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            # "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            # "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            # "scores": [
            #     {
            #         "word": "aoeu",
            #         "word_id": 2134,
            #         "presentation_count": 234,
            #         "correct_count": 234,
            #         "raw_score": 3.1416,
            #         "last_presentation": "yesterday when i was young"
            #     }
            # ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    # "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    # "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    # "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    # "correct_count": 234,
                    "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    # "raw_score": 3.1416,
                    "last_presentation": "yesterday when i was young"
                }
            ]
        },
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_name": "schindler",
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "word_id": 2134,
                    "presentation_count": 234,
                    "correct_count": 234,
                    "raw_score": 3.1416,
                    # "last_presentation": "yesterday when i was young"
                }
            ]
        },
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


class Test_QUIZ_RESPONSE_SCHEMA(unittest.TestCase):
    schema = js.QUIZ_RESPONSE_SCHEMA

    valid_docs = [
        {
            'quiz_id': 3,
            'word_id': 868,
            'word': 'Tarnung',
            'attrvalue': 'die',
            'attribute_id': 1,
            'correct_count': 0,
            'presentation_count': 0,
        }
    ]

    invalid_docs = [
        {
            # 'quiz_id': 3,
            'word_id': 868,
            'word': 'Tarnung',
            'attrvalue': 'die',
            'attribute_id': 1,
            'correct_count': 0,
            'presentation_count': 0,
        },
        {
            'quiz_id': 3,
            # 'word_id': 868,
            'word': 'Tarnung',
            'attrvalue': 'die',
            'attribute_id': 1,
            'correct_count': 0,
            'presentation_count': 0,
        },
        {
            'quiz_id': 3,
            'word_id': 868,
            # 'word': 'Tarnung',
            'attrvalue': 'die',
            'attribute_id': 1,
            'correct_count': 0,
            'presentation_count': 0,
        },
        {
            'quiz_id': 3,
            'word_id': 868,
            'word': 'Tarnung',
            # 'attrvalue': 'die',
            'attribute_id': 1,
            'correct_count': 0,
            'presentation_count': 0,
        },
        {
            'quiz_id': 3,
            'word_id': 868,
            'word': 'Tarnung',
            'attrvalue': 'die',
            # 'attribute_id': 1,
            'correct_count': 0,
            'presentation_count': 0,
        },
        {
            'quiz_id': 3,
            'word_id': 868,
            'word': 'Tarnung',
            'attrvalue': 'die',
            'attribute_id': 1,
            # 'correct_count': 0,
            'presentation_count': 0,
        },
        {
            'quiz_id': 3,
            'word_id': 868,
            'word': 'Tarnung',
            'attrvalue': 'die',
            'attribute_id': 1,
            'correct_count': 0,
            # 'presentation_count': 0,
        },
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


class Test_WORD_ADD_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = js.WORD_ADD_PAYLOAD_SCHEMA

    valid_docs = [
        {
            # fully specified payload
            "word": "werd",
            "pos_id": 1234,
            js.ATTRIBUTES: [
                {
                    "attribute_id": 1111,
                    "attrvalue": "value"
                },
                {
                    "attribute_id": 3243,
                    # attrvalue not required.
                }
            ]
        },
        {
            # without any attribute values is valid
            "word": "valid",
            "pos_id": 23,
        },
        {
            # empty attribute list is valid
            "word": "valid",
            "pos_id": 23,
            js.ATTRIBUTES: []
        }
    ]

    invalid_docs = [
        {
            # empty payload is not allowed
        },
        {
            # "word": "aoeu",
            "pos_id": 123
        },
        {
            "word": "aoeu",
            # "pos_id": 123
        },
        {
            "word": "",
            "pos_id": 1234
        },
        {
            "word": " ",
            "pos_id": 1234
        },
        {
            "word": "cannot have whitespace",
            "pos_id": 234
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            js.ATTRIBUTES: [
                {
                    # has to have an attribute id
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            js.ATTRIBUTES: [
                {
                    "attribute_id": "id has to be a string"
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            js.ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": ""
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            js.ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": "  "
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            js.ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": None
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            js.ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": 1234
                }
            ]
        },
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


class Test_WORD_UPDATE_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = js.WORD_UPDATE_PAYLOAD_SCHEMA

    valid_docs = [
        {
            # fully specified payload
            js.ATTRIBUTES: [
                {
                    "attribute_id": 1111,
                    "attrvalue": "value"
                },
                {
                    "attribute_id": 3243,
                    # attrvalue not required.
                }
            ]
        },
        {
            # empty payload is valid
        },
        {
            # empty attribute list is valid
            js.ATTRIBUTES: []
        }
    ]

    invalid_docs = [
        {
            js.ATTRIBUTES: [
                {
                    # has to have an attribute id
                }
            ]
        },
        {
            js.ATTRIBUTES: [
                {
                    "attribute_id": "id has to be a string"
                }
            ]
        },
        {
            js.ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": ""
                }
            ]
        },
        {
            js.ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": "  "
                }
            ]
        },
        {
            js.ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": None
                }
            ]
        },
        {
            js.ATTRIBUTES: [
                {
                    # attrvalue has to be a string
                    "attribute_id": 234,
                    "attrvalue": 1234
                }
            ]
        },
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
    schema = js.WORDS_RESPONSE_SCHEMA

    valid_docs = [
        [
            {
                "attributes": [
                    {'attrkey': 'definition',
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
    schema = js.WORDLIST_CONTENTS_PAYLOAD_SCHEMA

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


class Test_WORDLISTS_DELETE_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = js.WORDLISTS_DELETE_PAYLOAD_SCHEMA

    valid_docs = [
        [1, 2, 3],
        []
    ]

    invalid_docs = [
        {},
        "bullshit",
        ["more bullshit"]
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

    schema = js.WORDLIST_METADATA_PAYLOAD_SCHEMA

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
    schema = js.WORDLIST_METADATA_RESPONSE_SCHEMA

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
            "name": "bad list type",
            "sqlcode": "not really sql but what the hell",
            "citation": "  speeding  ",
            "list_type": "shopping"
        },
        {
            # bad id
            "wordlist_id": "1234",
            "name": "bad id",
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


class Test_WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = js.WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA

    valid_docs = [
        ["bingo", "bango", "bongo", "irving"],
        []
    ]

    invalid_docs = [
        ["no spaces allowed"],
        [1, 2, 3]
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

