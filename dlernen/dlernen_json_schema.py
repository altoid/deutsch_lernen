import jsonschema

##########################################################
#
#                   Patterns
#
##########################################################

STRING_PATTERN = r"""\S"""

# for names, leading/trailing whitespace is prohibited.
NAME_PATTERN = r"""^\S(.*\S)*$"""

WORD_PATTERN = r"""^\S+$"""

ID_PATTERN = WORD_PATTERN

# separate regex for multiline strings.
MULTILINE_STRING_PATTERN = r"""\S"""

ATTRIBUTES_ADDING = 'attributes_adding'
ATTRIBUTES_DELETING = 'attributes_deleting'
ATTRIBUTES_UPDATING = 'attributes_updating'

##########################################################
#
#                   NULL Schema
#
##########################################################

NULL_SCHEMA = {
    # to assist in creating test classes.  a doc with ANY content should not validate against this schema.
    # if we see this error we know we forgot to change the schema when we copy-pasted the test class.
    "type": "null"
}

##########################################################
#
#                   Payloads
#
##########################################################

REFRESH_WORDLISTS_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/refresh_wordlists",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload refreshing wordlists",
    "description": "Used for implementing POST to /api/wordlists",
    "type": "object",
    "required": [
        "word",
    ],
    "properties": {
        "word": {
            "type": "string",
            "pattern": WORD_PATTERN
        },
    }
}

WORD_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/updateword_payload",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for add/update word",
    "description": "Payload for add/update word",
    "type": "object",
    "required": [
        # no required fields
    ],
    "properties": {
        "word": {
            # this is optional but required when adding a word.
            "type": "string",
            "pattern": WORD_PATTERN
        },
        "pos_id": {
            # this is optional.  required for adding a word and ignored on updates
            "type": "integer",
            "minimum": 1
        },
        ATTRIBUTES_ADDING: {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "attrvalue",
                    "attribute_id"
                ],
                "properties": {
                    "attribute_id": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "attrvalue": {
                        "type": "string",
                        "pattern": STRING_PATTERN
                    }
                }
            }
        },
        ATTRIBUTES_DELETING: {
            "type": "array",
            "items": {
                "type": "integer",
                "minimum": 1
            }
        },
        ATTRIBUTES_UPDATING: {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "attrvalue",
                    "attrvalue_id"
                ],
                "properties": {
                    "attrvalue_id": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "attrvalue": {
                        "type": "string",
                        "pattern": STRING_PATTERN
                    }
                }
            }
        }
    }
}

# wordlist contents are notes and a list of words.

WORDLIST_CONTENTS_PAYLOAD_SCHEMA = {
    # can be used for add or update of a list.
    "$id": "https://deutsch-lernen.doug/schemas/addwordlist_payload",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "WORDLIST_CONTENTS_PAYLOAD_SCHEMA",
    "description": "Payload for adding content to a wordlist",
    "type": "object",
    "required": [
        # none are required.
    ],
    "properties": {
        "notes": {
            "type": ["string", 'null']
        },
        "words": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": WORD_PATTERN
            }
        }
    }
}

# wordlist metadata is all the info about a list except its contents.  metadata fields are:
#
#     - name
#     - id
#     - citation
#     - sqlcode
#     - type (empty, standard, smart.  derived value, not stored in database)
#

WORDLIST_METADATA_PAYLOAD_SCHEMA = {
    # can be used for add or update of a list.
    "$id": "https://deutsch-lernen.doug/schemas/addwordlist_payload",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for add wordlist",
    "description": "Payload for add wordlist",
    "type": "object",
    "required": [
        # haha, none are required.  string values must be at least 1 char if provided.
        # for creating a word list a name is of course required, but we will check that
        # in code, not here.
        #
        # we permit payloads with no name so that we can update a given list without having to specify a name.
    ],
    "properties": {
        "name": {
            "type": "string",
            "pattern": NAME_PATTERN
        },
        "citation": {
            "type": ["string", "null"],
            "pattern": STRING_PATTERN
        },
        "sqlcode": {
            "type": ["string", "null"],
            "pattern": MULTILINE_STRING_PATTERN
        }
    }
}

##########################################################
#
#                   Responses
#
##########################################################

POS_STRUCTURE_RESPONSE_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Part-of-Speech Structure",
    "description": """
    attributes for each part of speech, along with their sort ordering
    """,
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "pos_name",
            "pos_id",
            "attributes",
            "word",
            "word_id"
        ],
        "anyOf": [
            {"$ref": "#/$defs/word_info_null"},
            {"$ref": "#/$defs/word_info_not_null"},
        ],
    },

    "$defs": {
        "word_info_null": {
            "properties": {
                "pos_name": {
                    "type": "string"
                },
                "pos_id": {
                    "type": "integer",
                    "minimum": 0
                },
                "word": {
                    "type": "null",
                },
                "word_id": {
                    "type": "null",
                },
                "attributes": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": [
                            "attrkey",
                            "attribute_id",
                            "sort_order",
                            "attrvalue",
                            "attrvalue_id"
                        ],

                        "anyOf": [
                            # we require the attrvalue and attrvalue_id fields to be present.  both must be null,
                            # or both must be not null.  this is the only way enforce that.
                            {"$ref": "#/$attr_defs/attr_properties_null"},
                            # {"$ref": "#/$attr_defs/attr_properties_not_null"},
                        ]
                    }
                }
            }
        },
        "word_info_not_null": {
            "properties": {
                "pos_name": {
                    "type": "string"
                },
                "pos_id": {
                    "type": "integer",
                    "minimum": 0
                },
                "word": {
                    "type": "string"
                },
                "word_id": {
                    "type": "integer",
                    "minimum": 0
                },
                "attributes": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": [
                            "attrkey",
                            "attribute_id",
                            "sort_order",
                            "attrvalue",
                            "attrvalue_id"
                        ],

                        "anyOf": [
                            # we require the attrvalue and attrvalue_id fields to be present.  both must be null,
                            # or both must be not null.  this is the only way enforce that.
                            {"$ref": "#/$attr_defs/attr_properties_null"},
                            {"$ref": "#/$attr_defs/attr_properties_not_null"},
                        ]
                    }
                }
            }
        }
    },

    "$attr_defs": {
        "attr_properties_not_null": {
            "properties": {
                "attrkey": {
                    "type": "string"
                },
                "attribute_id": {
                    "type": "integer",
                    "minimum": 0
                },
                "sort_order": {
                    "type": "integer",
                    "minimum": 0
                },
                "attrvalue": {
                    "type": "string"
                },
                "attrvalue_id": {
                    "type": "integer",
                    "minimum": 0
                }
            }
        },
        "attr_properties_null": {
            "properties": {
                "attrkey": {
                    "type": "string"
                },
                "attribute_id": {
                    "type": "integer",
                    "minimum": 0
                },
                "sort_order": {
                    "type": "integer",
                    "minimum": 0
                },
                "attrvalue": {
                    "type": "null"
                },
                "attrvalue_id": {
                    "type": "null"
                }
            }
        }

    }
}

# TODO revisit this.  keys that are hardcoded values found in the database is a bad idea.
QUIZ_DATA_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/quiz_data",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Quiz Data List",
    "description": "list of quiz query results",
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "quiz_id",
            "word_id",
            "word"
        ],
        "properties": {
            "quiz_id": {
                "type": "integer",
                "minimum": 1
            },
            "word_id": {
                "type": "integer",
                "minimum": 1
            },
            "qname": {
                "type": "string"
            },
            "word": {
                "type": "string"
            },
            "attributes": {
                "type": "object",
                "properties": {
                    "article": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "plural": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "definition": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "first_person_singular": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "second_person_singular": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "third_person_singular": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "first_person_plural": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "second_person_plural": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "third_person_plural": {
                        "$ref": "#/$defs/quiz_attribute"
                    },
                    "past_participle": {
                        "$ref": "#/$defs/quiz_attribute"
                    }
                }
            }
        }
    },

    "$defs": {
        "quiz_attribute": {
            "type": "object",
            "properties": {
                "attrvalue": {
                    "type": "string"
                },
                "correct_count": {
                    "type": "integer",
                    "minimum": 0
                },
                "presentation_count": {
                    "type": "integer",
                    "minimum": 0
                },
                "attribute_id": {
                    "type": "integer",
                    "minimum": 1
                },
                "last_presentation": {
                    "type": ["string", "null"]
                }
            },
            "required": [
                "attrvalue",
                "attribute_id",
                "correct_count",
                "presentation_count",
                "last_presentation"
            ]
        }
    }
}

WORDLIST_METADATA_RESPONSE_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": """
    wordlist metadata is all the info about a list except its contents.
    """,
    "type": "object",
    "required": [
        "wordlist_id",
        "name",
        "sqlcode",
        "citation",
        "list_type"
    ],
    "properties": {
        "wordlist_id": {
            "type": "integer",
            "minimum": 1
        },
        "name": {
            "type": "string"
        },
        "sqlcode": {
            "type": ["string", "null"]
        },
        "citation": {
            "type": ["string", "null"]
        },
        "list_type": {
            "type": "string",
            "enum": [
                "smart",
                "standard",
                "empty"  # no code or words
            ]
        }
    }
}

WORDLIST_RESPONSE_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": """
    used for the response to GET /api/wordlist/<int:wordlist_id>, which is implemented in __get_wordlist().
    fully specifies a single word list.  defines the json documents that are returned when we do a get 
    request on a wordlist_id.  we get everything:
    - word list metadata
    - the notes
    - list type (smart, standard, empty)
    - all the words, known and unknown.
    note that we do not return the sqlcode if the list is a smart list.  we return the words fetched
    by the sql code.  which is the point of a smart list.
    """,
    "type": "object",
    "required": [
        "name",
        "wordlist_id",
        "list_type",
        "citation",
        "known_words",
        "unknown_words",
        "notes",
        "source_is_url"
    ],
    "properties": {
        "name": {
            "type": "string"
        },
        "wordlist_id": {
            "type": "integer",
            "minimum": 1
        },
        "list_type": {
            "type": "string",
            "enum": [
                "smart",
                "standard",
                "empty"  # no code or words
            ]
        },
        "citation": {
            "type": ["string", "null"]
        },
        "notes": {
            "type": ["string", "null"]
        },
        "source_is_url": {
            "type": "boolean"
        },
        "known_words": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["word", "word_id"],
                "properties": {
                    "word": {
                        "type": "string"
                    },
                    "word_id": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "article": {
                        "type": ["string", "null"]
                    },
                    "definition": {
                        "type": ["string", "null"]
                    }
                }
            }
        },
        "unknown_words": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    }
}

WORDLISTS_RESPONSE_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": """
    used for the result returned by get_wordlists.  returns an array of the following, for all of the wordlists in
    the database:
    - name
    - id
    - count of known words
    - list type (empty/smart/standard)
    """,
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string"
            },
            "wordlist_id": {
                "type": "integer",
                "minimum": 1
            },
            "count": {
                "type": "integer",
                "minimum": 0,
            },
            "list_type": {
                "type": "string",
                "enum": [
                    "smart",
                    "standard",
                    "empty"  # no code or words
                ]
            }
        },
        "required": [
            "name",
            "wordlist_id",
            "count",
            "list_type"
        ]
    }
}

WORDS_RESPONSE_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Word",
    "description": "list of words with attributes",
    "type": "array",
    "items": {
        "type": "object",
        "required": ["word", "word_id", "pos_name", "attributes"],
        "properties": {
            "word": {
                "type": "string"
            },
            "word_id": {
                "type": "integer",
                "minimum": 1
            },
            "pos_name": {
                "type": "string"
            },
            "attributes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["attrkey", "sort_order", "attrvalue", "attrvalue_id"],
                    "properties": {
                        "attrkey": {
                            "type": "string"
                        },
                        "sort_order": {
                            "type": "integer",
                            "minimum": 0
                        },
                        "attrvalue": {
                            "type": ["string", "null"]
                        },
                        "attrvalue_id": {
                            "type": ["integer", "null"]
                        }
                    }
                }
            }
        }
    }
    # the attributes - article, definition, etc. - are all optional but the attributes keyword is not.
}

