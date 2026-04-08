import unittest
import jsonschema
from dlernen.dlernen_json_schema import get_validator, ATTRIBUTES, \
    NULL_SCHEMA, \
    RELATION_PAYLOAD_SCHEMA, \
    WORD_ADD_PAYLOAD_SCHEMA, \
    WORD_UPDATE_PAYLOAD_SCHEMA, \
    WORDLIST_CONTENTS_PAYLOAD_SCHEMA, \
    WORDLISTS_DELETE_PAYLOAD_SCHEMA, \
    WORDLIST_METADATA_PAYLOAD_SCHEMA, \
    WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA, \
    POS_STRUCTURE_RESPONSE_SCHEMA, \
    QUIZ_ANSWER_PAYLOAD_SCHEMA, \
    QUIZ_REPORT_RESPONSE_SCHEMA, \
    QUIZ_RESPONSE_SCHEMA, \
    RELATION_RESPONSE_SCHEMA, \
    RELATION_RESPONSE_ARRAY_SCHEMA, \
    WORD_RESPONSE_SCHEMA, \
    WORD_RESPONSE_ARRAY_SCHEMA, \
    WORD_TAG_RESPONSE_SCHEMA, \
    WORDLIST_METADATA_RESPONSE_SCHEMA, \
    WORDLIST_RESPONSE_SCHEMA, \
    WORDLISTS_RESPONSE_SCHEMA

from pprint import pprint


# none of the tests here uses the API or hits the database.  these tests make sure that the JSONSCHEMA documents
# are defined correctly.


class Test_fiddling_with_referencing_and_registry(unittest.TestCase):
    def test1(self):
        # meh.  nothing new here.  jsonschema.Draft202012Validator is just an instance
        # of a validator.  validator_for will use a validator based on the $schema
        # in the schema object.

        validator_cls = get_validator(RELATION_RESPONSE_SCHEMA)
        validator_cls.check_schema(RELATION_RESPONSE_SCHEMA)

        # print(jsonschema.Draft202012Validator.META_SCHEMA["$id"])
        # pprint(RELATION_RESPONSE_SCHEMA['items']['required'])

        response = {
            'relation_id': 234,
            'words': [],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        }

        v = get_validator(RELATION_RESPONSE_SCHEMA)
        v.validate(response)

        response_arr = [response]

        v = get_validator(RELATION_RESPONSE_ARRAY_SCHEMA)
        v.validate(response_arr)


class Test_COPY_AND_PASTE_TO_CREATE_SCHEMA_TEST_CLASS(unittest.TestCase):
    schema = NULL_SCHEMA

    valid_docs = [
    ]

    invalid_docs = [
    ]

    #############################################################
    #
    # the jsonschema.validate method needs a schema against which it
    # can validate the data.  if you don't specify it via cls=
    # then it will figure it out from the $schema in the schema object.
    # more here:
    #
    # https://python-jsonschema.readthedocs.io/en/stable/api/#jsonschema.validate
    #
    #############################################################

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_POS_STRUCTURE_RESPONSE_SCHEMA(unittest.TestCase):
    schema = POS_STRUCTURE_RESPONSE_SCHEMA

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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_QUIZ_ANSWER_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = QUIZ_ANSWER_PAYLOAD_SCHEMA

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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_QUIZ_REPORT_RESPONSE_SCHEMA(unittest.TestCase):
    schema = QUIZ_REPORT_RESPONSE_SCHEMA

    valid_docs = [
        {
            "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [],
        },
    ]

    invalid_docs = [
        {
            # "quiz_key": "aoeu",
            "quiz_id": 234,
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
            # "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
            "wordlist_id": 234,
            # "scores": [
            #     {
            #         "word": "aoeu",
            #         "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [
                {
                    # "word": "aoeu",
                    "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    # "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
            "wordlist_id": 234,
            "scores": [
                {
                    "word": "aoeu",
                    "attrkey": "skeleton",
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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_QUIZ_RESPONSE_SCHEMA(unittest.TestCase):
    schema = QUIZ_RESPONSE_SCHEMA

    valid_docs = [
        [],
        [
            {
                'quiz_id': 3,
                'word_id': 868,
                'word': 'Tarnung',
                'attrvalue': 'die',
                'attribute_id': 1,
                'attrkey': 'whateverrr'
            },
            {
                'quiz_id': 3,
                'word_id': 868,
                'word': 'Tarnung',
                'attrvalue': None,
                'attribute_id': 1,
                'attrkey': 'null_attr_values_are_legit'
            },
        ]
    ]

    invalid_docs = [
        [
            {
                # 'quiz_id': 3,
                'word_id': 868,
                'word': 'Tarnung',
                'attrvalue': 'die',
                'attribute_id': 1,
                'attrkey': 'whateverrr'
            }
        ],
        [
            {
                'quiz_id': 3,
                # 'word_id': 868,
                'word': 'Tarnung',
                'attrvalue': 'die',
                'attribute_id': 1,
                'attrkey': 'whateverrr'
            }
        ],
        [
            {
                'quiz_id': 3,
                'word_id': 868,
                # 'word': 'Tarnung',
                'attrvalue': 'die',
                'attribute_id': 1,
                'attrkey': 'whateverrr'
            }
        ],
        [
            {
                'quiz_id': 3,
                'word_id': 868,
                'word': 'Tarnung',
                # 'attrvalue': 'die',
                'attribute_id': 1,
                'attrkey': 'whateverrr'
            }
        ],
        [
            {
                'quiz_id': 3,
                'word_id': 868,
                'word': 'Tarnung',
                'attrvalue': 'die',
                # 'attribute_id': 1,
                'attrkey': 'whateverrr'
            }
        ],
        [
            {
                'quiz_id': 3,
                'word_id': 868,
                'word': 'Tarnung',
                'attrvalue': 'die',
                'attribute_id': 1,
                # 'attrkey': 'whateverrr'
            }
        ],
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_RELATION_PAYLOAD_SCHEMA(unittest.TestCase):
    # nothing to test
    pass


class Test_RELATION_RESPONSE_SCHEMA(unittest.TestCase):
    schema = RELATION_RESPONSE_SCHEMA

    valid_docs = [
        {
            'relation_id': 234,
            'words': [
                {
                    'word': 'aoeu',
                    'word_id': 234,
                    'pos_name': 'aoeu',
                },
                {
                    'word': 'aoeu',
                    'word_id': 234,
                    'pos_name': 'aoeu',
                }
            ],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        },
        {
            'relation_id': 234,
            'words': [],
            'notes': None,
            'description': None
        }
    ]

    invalid_docs = [
        {
            'relation_id': 0,  # has to be > 0
            'words': [
                {
                    'word': 'aoeu',
                    'word_id': 234,
                    'pos_name': 'aoeu',
                },
            ],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        },
        {
            'relation_id': 11,
            'words': [
                {
                    'word': 'aoeu',
                    'word_id': 0,  # has to be > 0
                    'pos_name': 'aoeu',
                },
            ],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        },
        {
            # 'relation_id': 234,
            'words': [
                {
                    'word': 'aoeu',
                    'word_id': 234,
                    'pos_name': 'aoeu',
                },
            ],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        },
        {
            'relation_id': 234,
            # 'words': [
            #     {
            #         'word': 'aoeu',
            #         'word_id': 234,
            #         'pos_name': 'aoeu',
            #     },
            # ],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        },
        {
            'relation_id': 234,
            'words': [
                {
                    'word': 'aoeu',
                    'word_id': 234,
                    'pos_name': 'aoeu',
                },
            ],
            # 'notes': 'do re mi',
            'description': 'what this relation is for'
        },
        {
            'relation_id': 234,
            'words': [
                {
                    'word': 'aoeu',
                    'word_id': 234,
                    'pos_name': 'aoeu',
                },
            ],
            'notes': 'do re mi',
            # 'description': 'what this relation is for'
        },
        {
            'relation_id': 234,
            'words': [
                {
                    # 'word': 'aoeu',
                    'word_id': 234,
                    'pos_name': 'aoeu',
                },
            ],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        },
        {
            'relation_id': 234,
            'words': [
                {
                    'word': 'aoeu',
                    # 'word_id': 234,
                    'pos_name': 'aoeu',
                },
            ],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        },
        {
            'relation_id': 234,
            'words': [
                {
                    'word': 'aoeu',
                    'word_id': 234,
                    # 'pos_name': 'aoeu',
                },
            ],
            'notes': 'do re mi',
            'description': 'what this relation is for'
        },
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_RELATION_ARRAY_RESPONSE_SCHEMA(unittest.TestCase):
    schema = RELATION_RESPONSE_ARRAY_SCHEMA

    def test_valid_docs(self):
        get_validator(self.schema).validate(Test_RELATION_RESPONSE_SCHEMA.valid_docs)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORD_RESPONSE_SCHEMA(unittest.TestCase):
    schema = WORD_RESPONSE_SCHEMA

    valid_docs = [
        {
            "word": "saoethus",
            "word_id": 1234,
            "pos_name": "eoui",
            "notes": "this is a cool word",
            "attributes": [
                {
                    'attrkey': 'definition',
                    'sort_order': 5,
                    'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },
        {
            "word": "saoethus",
            "word_id": 1234,
            "pos_name": "eoui",
            "notes": None,
            "attributes": [
            ],
        },
    ]

    invalid_docs = [
        {
            "word": "saoethus",
            "word_id": "1234",
            "pos_name": "eoui",
            "notes": "this is a cool word",
            "attributes": [
                {
                    'attrkey': 'definition',
                    'sort_order': 5,
                    'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },
        {
            # "word": "saoethus",
            "word_id": 1234,
            "pos_name": "eoui",
            "notes": "this is a cool word",
            "attributes": [
                {
                    'attrkey': 'definition',
                    'sort_order': 5,
                    'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },
        {
            "word": "saoethus",
            # "word_id": 1234,
            "pos_name": "eoui",
            "notes": "this is a cool word",
            "attributes": [
                {
                    'attrkey': 'definition',
                    'sort_order': 5,
                    'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },
        {
            "word": "saoethus",
            "word_id": 1234,
            # "pos_name": "eoui",
            "notes": "this is a cool word",
            "attributes": [
                {
                    'attrkey': 'definition',
                    'sort_order': 5,
                    'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },
        {
            "word": "saoethus",
            "word_id": 1234,
            "pos_name": "eoui",
            # "notes": "this is a cool word",
            "attributes": [
                {
                    'attrkey': 'definition',
                    'sort_order': 5,
                    'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },
        {
            "word": "saoethus",
            "word_id": 1234,
            "pos_name": "eoui",
            "notes": "this is a cool word",
            # "attributes": [
            #     {
            #         'attrkey': 'definition',
            #         'sort_order': 5,
            #         'attrvalue': 'to spoil, deteriorate, go bad'
            #     },
            # ],
        },
        {
            "word": "saoethus",
            "word_id": 1234,
            "pos_name": "eoui",
            "notes": "this is a cool word",
            "attributes": [
                {
                    # 'attrkey': 'definition',
                    'sort_order': 5,
                    'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },
        {
            "word": "saoethus",
            "word_id": 1234,
            "pos_name": "eoui",
            "notes": "this is a cool word",
            "attributes": [
                {
                    'attrkey': 'definition',
                    # 'sort_order': 5,
                    'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },
        {
            "word": "saoethus",
            "word_id": 1234,
            "pos_name": "eoui",
            "notes": "this is a cool word",
            "attributes": [
                {
                    'attrkey': 'definition',
                    'sort_order': 5,
                    # 'attrvalue': 'to spoil, deteriorate, go bad'
                },
            ],
        },

    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORD_ARRAY_RESPONSE_SCHEMA(unittest.TestCase):
    schema = WORD_RESPONSE_ARRAY_SCHEMA

    def test_valid_docs(self):
        get_validator(self.schema).validate(Test_WORD_RESPONSE_SCHEMA.valid_docs)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORD_ADD_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = WORD_ADD_PAYLOAD_SCHEMA

    valid_docs = [
        {
            # fully specified payload
            "word": "werd",
            "pos_id": 1234,
            "notes": "do re mi",
            ATTRIBUTES: [
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
            "notes": None,
        },
        {
            # empty attribute list is valid
            "word": "valid",
            "pos_id": 23,
            "notes": "whatevs",
            ATTRIBUTES: []
        }
    ]

    invalid_docs = [
        {
            # empty payload is not allowed
        },
        {
            # "word": "aoeu",
            "pos_id": 123,
            "notes": "boo boo",
        },
        {
            "word": "aoeu",
            # "pos_id": 123,
            "notes": "boo boo",
        },
        {
            "word": "",
            "pos_id": 1234,
            "notes": "boo boo",
        },
        {
            "word": " ",
            "pos_id": 1234,
            "notes": "",
        },
        {
            "word": "cannot have whitespace",
            "pos_id": 234,
            "notes": "boo boo",
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    # has to have an attribute id
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attribute_id": "id has to be a string"
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": ""
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": "  "
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": None
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_id": 234,
            "notes": "boo boo",
            ATTRIBUTES: [
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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORD_TAG_RESPONSE_SCHEMA(unittest.TestCase):
    schema = WORD_TAG_RESPONSE_SCHEMA

    valid_docs = [
        {
            "wordlist_id": 1234,
            "word_id": 234,
            "tags": [
                "one", "two", "aoeu"
            ]
        },
        {
            "wordlist_id": 1234,
            "tags": [
                "word_id", "not", "required"
            ]
        },
    ]

    invalid_docs = [
        {
            # "wordlist_id": 1234,
            "word_id": 234,
            "tags": [
                "one", "two", "aoeu"
            ]
        },
        {
            "wordlist_id": 1234,
            "word_id": 234,
            # "tags": [
            #     "one", "two", "aoeu"
            # ]
        },
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORD_UPDATE_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = WORD_UPDATE_PAYLOAD_SCHEMA

    valid_docs = [
        {
            # fully specified payload
            "word": "werrrd",
            "notes": "boo boo",
            ATTRIBUTES: [
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
            ATTRIBUTES: []
        },
        {
            # empty notes is valid
            "notes": None
        },
        {
            # empty notes is valid
            "notes": ""
        }
    ]

    invalid_docs = [
        {
            ATTRIBUTES: [
                {
                    # has to have an attribute id
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    "attribute_id": "id has to be a string"
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": ""
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": "  "
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    "attribute_id": 234,
                    "attrvalue": None
                }
            ]
        },
        {
            ATTRIBUTES: [
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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_CONTENTS_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = WORDLIST_CONTENTS_PAYLOAD_SCHEMA

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
            "word_ids": []  # empty list is valid
        },
        {
            "word_ids": [
                123,
                234,
                345
            ]
        },
        {
            "notes": "whatevs",
            "word_ids": [
                11,
                22
            ]
        }
    ]

    invalid_docs = [
        {
            "word_ids": [
                "word_ids have to",
                "be integers"
            ]
        }
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_METADATA_PAYLOAD_SCHEMA(unittest.TestCase):
    # note:  these tests don't validate sqlcode.  that happens in the API tests.

    schema = WORDLIST_METADATA_PAYLOAD_SCHEMA

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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_METADATA_RESPONSE_SCHEMA(unittest.TestCase):
    schema = WORDLIST_METADATA_RESPONSE_SCHEMA

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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_responses:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_RESPONSE_SCHEMA(unittest.TestCase):
    schema = WORDLIST_RESPONSE_SCHEMA

    valid_docs = [
        {'citation': None,
         'words': [{'article': None,
                    'definition': "it's an adjective",
                    'word': 'anohteduntaheoud',
                    'pos_name': 'its_a_pos',
                    'tags': [],
                    'word_id': 9185},
                   {'article': None,
                    'definition': "no it's a floor cleaner",
                    'word': 'anohteduntaheoud',
                    'pos_name': 'its_a_pos',
                    'tags': ['abcd'],
                    'word_id': 9186},
                   {'article': None,
                    'definition': "now it's a noun",
                    'word': 'Anohteduntaheoud',
                    'pos_name': 'its_a_pos',
                    'tags': [],
                    'word_id': 9187},
                   {'article': None,
                    'definition': None,  # null is OK
                    'word': 'anohteduntaheoud',
                    'pos_name': 'its_a_pos',
                    'tags': [],
                    'word_id': 9188},
                   {'article': None,
                    'definition': "look it's a verb",
                    'pos_name': 'its_a_pos',
                    'word': 'anohteduntaheoud',
                    'tags': ['fish', 'heads'],
                    'word_id': 9189}],
         'list_type': 'standard',
         'name': 'aaa fake list 1',
         'notes': None,
         'source_is_url': False,
         'sqlcode': None,
         'wordlist_id': 4237},
        {
            "name": "sample_word_list",
            "wordlist_id": 1234,
            "list_type": "standard",
            "words": [
                {
                    "word": "aoeuaeou",
                    'pos_name': 'its_a_pos',
                    "word_id": 123,
                    "tags": ["aoeu"],
                    "definition": "hell if i know"
                },
                {
                    "word": "Iethdsenihtd",
                    'pos_name': 'its_a_pos',
                    "word_id": 465,
                    "article": "das",
                    "tags": ["aoeu", "oeui"],
                    "definition": "an odd noun"
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 1234,
            "list_type": "standard",
            "words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "null citation and notes",
            "wordlist_id": 1234,
            "list_type": "standard",
            "words": [],
            "citation": None,
            "source_is_url": False,
            "notes": None
        }
    ]

    invalid_docs = [
        {
            "name": "bullshit list type",
            "wordlist_id": 1,
            "list_type": "bullshit",
            "words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            # "name": "no words",
            "wordlist_id": 2,
            "list_type": "standard",
            "words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "no name"
        },
        {
            "name": "no words",
            # "wordlist_id": 3,
            "list_type": "standard",
            "words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 4,
            # "list_type": "standard",
            "words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 5,
            "list_type": "standard",
            # "words": [],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 6,
            "list_type": "standard",
            "words": [],
            # "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 7,
            "list_type": "standard",
            "words": [],
            "citation": "where i got this",
            # "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "no words",
            "wordlist_id": 8,
            "list_type": "standard",
            "words": [],
            "citation": "where i got this",
            "source_is_url": False,
            # "notes": "lots of stuff"
        },
        {
            "name": "messin with words",
            "wordlist_id": 9,
            "list_type": "standard",
            "words": [
                {
                    # "word": "werrd",
                    "word_id": 1234,
                    "tags": ["egad"],
                    'pos_name': 'its_a_pos',
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "messin with words",
            "wordlist_id": 10,
            "list_type": "standard",
            "words": [
                {
                    "word": "werrd",
                    # "word_id": 1234,
                    "tags": ["egad"],
                    'pos_name': 'its_a_pos',
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            "name": "messin with words",
            "wordlist_id": 12,
            "list_type": "standard",
            "words": [
                {
                    "word": "werrd",
                    "word_id": 1234,
                    "tags": ["egad"],
                    # 'pos_name': 'its_a_pos',
                }
            ],
            "citation": "where i got this",
            "source_is_url": False,
            "notes": "lots of stuff"
        },
        {
            # empty doc not allowed
        }
    ]

    def test_valid_docs(self):
        for jdoc in self.valid_docs:
            with self.subTest(jdoc=jdoc):
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA

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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLISTS_DELETE_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = WORDLISTS_DELETE_PAYLOAD_SCHEMA

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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)


class Test_WORDLISTS_RESPONSE_SCHEMA(unittest.TestCase):
    schema = WORDLISTS_RESPONSE_SCHEMA

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
                get_validator(self.schema).validate(jdoc)

    def test_invalid_docs(self):
        for jdoc in self.invalid_docs:
            with self.subTest(jdoc=jdoc):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    get_validator(self.schema).validate(jdoc)

    def test_check_schema(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)
