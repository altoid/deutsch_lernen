import unittest
import jsonschema
from dlernen.dlernen_json_schema import get_validator, ATTRIBUTES, \
    NULL_SCHEMA, \
    WORDLIST_PAYLOAD_SCHEMA, \
    WORD_ADD_PAYLOAD_SCHEMA, \
    WORD_UPDATE_PAYLOAD_SCHEMA, \
    WORDLISTS_DELETE_PAYLOAD_SCHEMA, \
    WORDLIST_TAG_PAYLOAD_SCHEMA, \
    POS_STRUCTURE_RESPONSE_SCHEMA, \
    PREFIX_VERB_RESPONSE_SCHEMA, \
    QUIZ_ANSWER_PAYLOAD_SCHEMA, \
    QUIZ_REPORT_RESPONSE_SCHEMA, \
    QUIZ_RESPONSE_SCHEMA, \
    RELATION_RESPONSE_SCHEMA, \
    ARRAY_RELATION_RESPONSE_SCHEMA, \
    WORD_RESPONSE_SCHEMA, \
    ARRAY_WORD_RESPONSE_SCHEMA, \
    WORD_TAG_RESPONSE_SCHEMA, \
    WORDLIST_METADATA_RESPONSE_SCHEMA, \
    WORDLIST_RESPONSE_SCHEMA

from pprint import pprint


# none of the tests here uses the API or hits the database.  these tests make sure that the JSONSCHEMA documents
# are defined correctly.


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


class Test_QUIZ_REPORT_RESPONSE_SCHEMA_2(unittest.TestCase):
    schema = QUIZ_REPORT_RESPONSE_SCHEMA

    valid_docs = [
        {
            'quiz_key': 'jerky',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'aoeu',
                            'attribute_id': 1,
                            'sort_order': 1,
                            'correct_count': 1,  # >= 0
                            'presentation_count': 1,
                            'raw_score': 1.11,  # type is 'number'
                            'last_presentation': 'string-valued'  # ifnull(last_presentation, '--') in sql
                        },
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
                {
                    'word': 'fooble',
                    'word_id': 12,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'aoeu',
                            'attribute_id': 1,
                            'sort_order': 1,
                            'correct_count': 1,  # >= 0
                            'presentation_count': 1,
                            'raw_score': 1.11,  # type is 'number'
                            'last_presentation': '--'
                        },
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'herky',
            'quiz_id': 2,
            'wordlist_id': 2,
            'words': [
                # ok to have no words
            ]
        }
    ]

    invalid_docs = [
        # missing fields
        {
            # 'quiz_key': 'number1',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number2',
            # 'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number3',
            'quiz_id': 1,
            # 'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number4',
            'quiz_id': 1,
            'wordlist_id': 1,
            # 'words': [
            #     {
            #         'word': 'wat',
            #         'word_id': 1,
            #         'attributes': [  # minItems is 1
            #             {
            #                 'attrkey': 'blabla',
            #                 'attribute_id': 2,
            #                 'sort_order': 2,
            #                 'correct_count': 0,  # >= 0
            #                 'presentation_count': 18,  # just forgetful i guess
            #                 'raw_score': 0.0,  # type is 'number'
            #                 'last_presentation': 'string-valued'
            #             },
            #         ]
            #     },
            # ]
        },
        {
            'quiz_key': 'number5',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    # 'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number6',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    # 'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number7',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    # 'attributes': [  # minItems is 1
                    #     {
                    #         'attrkey': 'blabla',
                    #         'attribute_id': 2,
                    #         'sort_order': 2,
                    #         'correct_count': 0,  # >= 0
                    #         'presentation_count': 18,  # just forgetful i guess
                    #         'raw_score': 0.0,  # type is 'number'
                    #         'last_presentation': 'string-valued'
                    #     },
                    # ]
                },
            ]
        },
        {
            'quiz_key': 'number8',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            # 'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number9',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            # 'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number10',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            # 'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number11',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            # 'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number12',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            # 'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number13',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            # 'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },
        {
            'quiz_key': 'number14',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            # 'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },

        # must have at least one attribute for a word
        {
            'quiz_key': 'number15',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                    ]
                },
            ]
        },

        # stowaway in top-level doc
        {
            'quiz_key': 'number16',
            'quiz_id': 1,
            'gotAnyGrapes': True,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },

        # stowaway in word
        {
            'quiz_key': 'number17',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'gotAnyGrapes': True,
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
            ]
        },

        # stowaway in attribute
        {
            'quiz_key': 'number18',
            'quiz_id': 1,
            'wordlist_id': 1,
            'words': [
                {
                    'word': 'wat',
                    'word_id': 1,
                    'attributes': [  # minItems is 1
                        {
                            'gotAnyGrapes': True,
                            'attrkey': 'blabla',
                            'attribute_id': 2,
                            'sort_order': 2,
                            'correct_count': 0,  # >= 0
                            'presentation_count': 18,  # just forgetful i guess
                            'raw_score': 0.0,  # type is 'number'
                            'last_presentation': 'string-valued'
                        },
                    ]
                },
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


class Test_PREFIX_VERB_RESPONSE_SCHEMA(unittest.TestCase):
    schema = PREFIX_VERB_RESPONSE_SCHEMA

    valid_docs = [
        {
            "grundverb_word_id": 1111,
            "word_id": 1111,
            "prefix": "pre",
            "prefix_word_id": 1111,
            "prefix_pos_name": "aoeu"
        },
        {
            "grundverb_word_id": 2222,
            "word_id": 2222,
            "prefix": "pre",
            "prefix_word_id": None,
            "prefix_pos_name": "aoeu"
        },
    ]

    invalid_docs = [
        {
            # "grundverb_word_id": 1111,
            "word_id": 11112,
            "prefix": "pre",
            "prefix_word_id": 11112,
            "prefix_pos_name": "aoeu"
        },
        {
            "grundverb_word_id": 11113,
            # "word_id": 1111,
            "prefix": "pre",
            "prefix_word_id": 11113,
            "prefix_pos_name": "aoeu"
        },
        {
            "grundverb_word_id": 11114,
            "word_id": 11114,
            # "prefix": "pre",
            "prefix_word_id": 11114,
            "prefix_pos_name": "aoeu"
        },
        {
            "grundverb_word_id": 11115,
            "word_id": 11115,
            "prefix": "pre",
            # "prefix_word_id": 1111,
            "prefix_pos_name": "aoeu"
        },
        {
            "grundverb_word_id": 11116,
            "word_id": 11116,
            "prefix": "pre",
            "prefix_word_id": 11116,
            # "prefix_pos_name": "aoeu"
        },
        {
            "grundverb_word_id": 11117,
            "word_id": 11117,
            "prefix": None,  # can't be none
            "prefix_word_id": 11117,
            "prefix_pos_name": "aoeu"
        },
        {
            "grundverb_word_id": 11118,
            "word_id": 11118,
            "prefix": "",  # can't be empty
            "prefix_word_id": 11118,
            "prefix_pos_name": "aoeu"
        },
        {
            "grundverb_word_id": 11119,
            "word_id": 11119,
            "prefix": "uuuu",
            "prefix_word_id": 11119,
            "prefix_pos_name": None  # can't be none
        },
        {
            "grundverb_word_id": 11110,
            "word_id": 11110,
            "prefix": "uuuu",
            "prefix_word_id": 11110,
            "prefix_pos_name": ""  # can't be empty
        },
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


class Test_WORDLIST_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = WORDLIST_PAYLOAD_SCHEMA

    valid_docs = [
        {
            "sqlcode": "whee",
        },
        {
            "word_ids": [1, 2, 3]
        },
        {
            "name": "aoeu"
        },
        {
            # empty payload is ok.
        },
        {
            "name": "saetuasasue",
            "citation": "anteohusntaeo",
            "sqlcode": "n;sercisr;cih"
        },
        {
            "name": "saetuasasue",
            "citation": None,
            "sqlcode": None,
            "notes": None
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
            # sqlcode and word_ids can't both be present.
            "sqlcode": "whee",
            "word_ids": [1, 2, 3]
        },
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
        },
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


class Test_QUIZ_ANSWER_PAYLOAD_SCHEMA_2(unittest.TestCase):
    schema = QUIZ_ANSWER_PAYLOAD_SCHEMA

    valid_docs = [
        {
            'word_id': 1,
            'attribute_id': 1,
            'correct': True
        },
        {
            'word_id': 2,
            'attribute_id': 2,
            'correct': False
        },
    ]

    invalid_docs = [
        {
            'extra_field': 8,
            'word_id': 8,
            'attribute_id': 8,
            'correct': True,
        },
        {
            # 'word_id': 3,
            'attribute_id': 3,
            'correct': True,
        },
        {
            'word_id': 5,
            # 'attribute_id': 5,
            'correct': True,
        },
        {
            'word_id': 6,
            'attribute_id': 6,
            # 'correct': True,
        },
        {
            'word_id': 7,
            'attribute_id': 7,
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


class Test_QUIZ_RESPONSE_SCHEMA(unittest.TestCase):
    schema = QUIZ_RESPONSE_SCHEMA

    valid_docs = [
        {
            'quiz_id': 1,
            'word_id': 1,
            'word': 'assdribble',
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 1,
                    'attrvalue': 'whatevs',
                    'sort_order': 1
                }
            ]
        },
        {
            'quiz_id': 2,
            'word_id': 2,
            'word': 'assdribble',
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 2,
                    'attrvalue': 'multiple attributes',
                    'sort_order': 2
                },
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 3,
                    'attrvalue': None,  # null values are kosher
                    'sort_order': 3
                },
            ]
        },
    ]

    invalid_docs = [
        {
            'word': 'nthedunaethdu',
            'quiz_id': 111,
            'word_id': 111,
            'pos_name': '',   # must conform to STRING_PATTERN
            ATTRIBUTES: [
                {
                    'attribute_id': 111,
                    'attrvalue': 'whatevs',
                    'sort_order': 111,
                    'attrkey': 'bubbles',
                }
            ]
        },
        {
            'word': '',  # must conform to WORD_PATTERN
            'quiz_id': 111,
            'word_id': 111,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attribute_id': 111,
                    'attrvalue': 'whatevs',
                    'sort_order': 111,
                    'attrkey': 'bubbles',
                }
            ]
        },
        # all the missing fields
        {
            # 'word': 'dribble',
            'quiz_id': 10,
            'word_id': 10,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attribute_id': 10,
                    'attrvalue': 'whatevs',
                    'sort_order': 10,
                    'attrkey': 'bubbles',
                }
            ]
        },
        {
            'word': 'dribble',
            # 'quiz_id': 1,
            'word_id': 1,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attribute_id': 1,
                    'attrvalue': 'whatevs',
                    'sort_order': 1,
                    'attrkey': 'bubbles',
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 2,
            # 'word_id': 2,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 2,
                    'sort_order': 2,
                    'attrvalue': 'whatevs'
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 2,
            'word_id': 2,
            # 'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 2,
                    'sort_order': 2,
                    'attrvalue': 'whatevs'
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 3,
            'word_id': 3,
            'pos_name': 'pozz',
            # ATTRIBUTES: [
            #     {
            #         'attrkey': 'bubbles',
            #         'attribute_id': 3,
            #         'sort_order': 3,
            #         'attrvalue': 'whatevs'
            #     }
            # ]
        },
        {
            'word': 'dribble',
            'quiz_id': 4,
            'word_id': 4,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                # need at least 1
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 55,
            'word_id': 55,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    # 'attrkey': 'bubbles',
                    'attribute_id': 5,
                    'sort_order': 5,
                    'attrvalue': 'whatevs'
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 5,
            'word_id': 5,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    # 'attribute_id': 5,
                    'sort_order': 5,
                    'attrvalue': 'whatevs'
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 55,
            'word_id': 55,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 55,
                    # 'sort_order': 55,
                    'attrvalue': 'whatevs'
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 6,
            'word_id': 6,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 6,
                    'sort_order': 6,
                    # 'attrvalue': 'whatevs'
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 7,
            'word_id': 7,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 7,
                    'sort_order': 7,
                    'attrvalue': ''  # can't be empty
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 77,
            'word_id': 77,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 77,
                    'sort_order': 77,
                    'attrvalue': '      '  # whitespace-only not allowed
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 88,
            'word_id': 88,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': '',  # must conform to ID_PATTERN
                    'attribute_id': 88,
                    'sort_order': 88,
                    'attrvalue': 'aoeu'
                }
            ]
        },
        {
            'word': 'dribble',
            'quiz_id': 9,
            'word_id': 9,
            'pos_name': 'pozz',
            ATTRIBUTES: [
                {
                    'attrkey': 'bubbles',
                    'attribute_id': 9,
                    'stowaway': 'bleep',
                    'sort_order': 9,
                    'attrvalue': 'aoeu'
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
    schema = ARRAY_RELATION_RESPONSE_SCHEMA

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
                    'attrvalue': 'to spoil, deteriorate, go bad',
                    'attribute_id': 5,
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
            "word_id": "1234",   # should be int
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
                    'attribute_id': 22,
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
                    'attribute_id': 22,
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
                    'attribute_id': 22,
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
                    'attribute_id': 22,
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
            #         'attribute_id': 22,
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
                    # 'attribute_id': 22,
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
            "attributes": [
                {
                    'attribute_id': 22,
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
                    'attribute_id': 22,
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
                    'attribute_id': 22,
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
    schema = ARRAY_WORD_RESPONSE_SCHEMA

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
            "pos_name": "boobs",
            "notes": "do re mi",
            ATTRIBUTES: [
                {
                    "attrkey": "aoeuaoeu",
                    "attrvalue": "value"
                },
                {
                    "attrkey": "aoeuaoeu",
                    # attrvalue not required.
                }
            ]
        },
        {
            # without any attribute values is valid
            "word": "valid",
            "pos_name": "boobs",
            "notes": None,
        },
        {
            # empty attribute list is valid
            "word": "valid",
            "pos_name": "boobs",
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
            "pos_name": "boobs",
            "notes": "boo boo",
        },
        {
            "word": "aoeu",
            # "pos_name": "boobs",
            "notes": "boo boo",
        },
        {
            "word": "",
            "pos_name": "boobs",
            "notes": "boo boo",
        },
        {
            "word": " ",
            "pos_name": "boobs",
            "notes": "",
        },
        {
            "word": "cannot have whitespace",
            "pos_name": "boobs",
            "notes": "boo boo",
        },
        {
            "word": "aoeu",
            "pos_name": "boobs",
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    # has to have an attrkey
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_name": "boobs",
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attrkey": "key cannot have whitespace"
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_name": "boobs",
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attrkey": "aoeuaoeu",
                    "attrvalue": ""
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_name": "boobs",
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attrkey": "whatevs",
                    "attrvalue": "  "
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_name": "boobs",
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attrkey": "whatevs",
                    "attrvalue": None
                }
            ]
        },
        {
            "word": "aoeu",
            "pos_name": "boobs",
            "notes": "boo boo",
            ATTRIBUTES: [
                {
                    "attrkey": "whatevs",
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
                    "attrkey": "aoeuaoeu",
                    "attrvalue": "value"
                },
                {
                    "attrkey": "aoeuaoeu",
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
                    # has to have an attrkey
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    "attrkey": "key cannot have whitespace"
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    "attrkey": "whatevs",
                    "attrvalue": ""
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    "attrkey": "whatevs",
                    "attrvalue": "  "
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    "attrkey": "whatevs",
                    "attrvalue": None
                }
            ]
        },
        {
            ATTRIBUTES: [
                {
                    # attrvalue has to be a string
                    "attrkey": "whatevs",
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


class Test_WORDLIST_METADATA_RESPONSE_SCHEMA(unittest.TestCase):
    schema = WORDLIST_METADATA_RESPONSE_SCHEMA

    valid_responses = [
        {
            "wordlist_id": 1234,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "  speeding  ",
            "list_type": "empty",
            "count": 42
        },
        {
            "wordlist_id": 1234,
            "name": "fester",
            "sqlcode": None,
            "citation": None,
            "list_type": "empty",
            "count": 0
        }
    ]

    invalid_responses = [
        # any required fields not present should cause validation error
        {
            # "wordlist_id": 1,
            "name": "missing id",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty",
            "count": 0
        },
        {
            "wordlist_id": 2,
            # "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty",
            "count": 0
        },
        {
            "wordlist_id": 3,
            "name": "fester",
            # "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty",
            "count": 0
        },
        {
            "wordlist_id": 4,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            # "citation": "speeding",
            "list_type": "empty",
            "count": 0
        },
        {
            "wordlist_id": 5,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            # "list_type": "empty",
            "count": 0
        },
        {
            "wordlist_id": 55,
            "name": "fester",
            "sqlcode": "not really sql but what the hell",
            "citation": "speeding",
            "list_type": "empty",
            # "count": 0
        },
        {
            # bad list type
            "wordlist_id": 6,
            "name": "bad list type",
            "sqlcode": "not really sql but what the hell",
            "citation": "  speeding  ",
            "list_type": "shopping",
            "count": 0
        },
        {
            # bad id
            "wordlist_id": "1234",
            "name": "bad id",
            "sqlcode": "not really sql but what the hell",
            "citation": "aoeuoea",
            "list_type": "empty",
            "count": 0
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


class Test_WORDLIST_TAG_PAYLOAD_SCHEMA(unittest.TestCase):
    schema = WORDLIST_TAG_PAYLOAD_SCHEMA

    valid_docs = [
        [
            {
                'word_id': 1,
                'tags': ["bingo", "bango", "bongo", "irving"]
            },
            {
                'word_id': 2,
                'tags': ["bingo", "bango", "bongo", "irving"]
            },
        ],
        [
            {
                'word_id': 3,
                'tags': []
            },
        ],
        [
            # 0-length array is ok.  stupid, but ok.
        ]
    ]

    invalid_docs = [
        [
            {
                # 'word_id': 4,
                'tags': []
            },
        ],
        [
            {
                'word_id': 5,
                # 'tags': []
            },
        ]
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
