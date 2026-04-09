import jsonschema
from referencing import Registry, Resource

#
#
#
#                       hhhhhhh
#                       h:::::h
#                       h:::::h
#                       h:::::h
#                        h::::h hhhhh           eeeeeeeeeeee  yyyyyyy           yyyyyyy
#                        h::::hh:::::hhh      ee::::::::::::ee y:::::y         y:::::y
#                        h::::::::::::::hh   e::::::eeeee:::::eey:::::y       y:::::y
#                        h:::::::hhh::::::h e::::::e     e:::::e y:::::y     y:::::y
#                        h::::::h   h::::::he:::::::eeeee::::::e  y:::::y   y:::::y
#                        h:::::h     h:::::he:::::::::::::::::e    y:::::y y:::::y
#                        h:::::h     h:::::he::::::eeeeeeeeeee      y:::::y:::::y
#                        h:::::h     h:::::he:::::::e                y:::::::::y
#                        h:::::h     h:::::he::::::::e                y:::::::y
#                        h:::::h     h:::::h e::::::::eeeeeeee         y:::::y
#                        h:::::h     h:::::h  ee:::::::::::::e        y:::::y
#                        hhhhhhh     hhhhhhh    eeeeeeeeeeeeee       y:::::y
#                                                                   y:::::y
#                                                                  y:::::y
#                                                                 y:::::y
#                                                                y:::::y
#                                                               yyyyyyy
#
#
# whenever you add/remove a json schema object, you have to do the following:
#
# - modify the registry, which is at the end of this file.
# - add a test case to tests_schema.py
#
#

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

ATTRIBUTES = 'attributes'

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
#                   helper schemata
#
##########################################################

DISPLAYABLE_WORD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/displayable_word.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist Word",
    "description": """
    everything about a wordlist member word that we need to render it in a page.

    this is not used as a payload or as a response, but is referred to by WORDLIST_RESPONSE_SCHEMA.
    """,
    "type": "object",
    "required": [
        "word",
        "word_id",
        # "tags",
        "pos_name"
    ],
    "additionalProperties": False,
    "properties": {
        "word": {
            "type": "string"
        },
        "pos_name": {
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
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    }
}

ARRAY_DISPLAYABLE_WORD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/array_displayable_word.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Displayable Word",
    "description": "array of DISPLAYABLE_WORD",
    "type": "array",
    "items": {
        "$ref": DISPLAYABLE_WORD_SCHEMA["$id"]
    }
}

##########################################################
#
#                   Payloads
#
##########################################################

RELATION_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/relation_payload.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "payload for creating/updating a relation",
    "description": """
    payload for creating/updating a relation
    """,
    "type": "object",
    "required": [
        # none of these is required.  creating a relation with an empty payload is ok.  we will have
        # a relation with an id but no content.
        # "word_ids",
        # "notes",
        # "description"
    ],
    "additionalProperties": False,
    "properties": {
        "word_ids": {
            "type": "array",
            "items": {
                "type": "integer"
            }
        },
        "notes": {
            "type": ["string", 'null']
        },
        "description": {
            "type": ["string", 'null']
        }
    }
}

WORD_ATTRIBUTES_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/word_attributes.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Schema for word attributes in a payload",
    "description": """describes the structure of word attributes in an add or update
    payload.  this is not intended to be used by itself in requests, it just describes the
    structure of word attributes common to both word add and update payloads.
    """,
    "type": "object",
    "required": [
        "attribute_id"
        # attrvalue is not required.  if not provided, the attribute is deleted.
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

WORD_ADD_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/word_add_payload.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for add word",
    "description": "Payload for add word",
    "type": "object",
    "required": [
        "word",
        "pos_id"
    ],
    "additionalProperties": False,
    "properties": {
        "word": {
            "type": "string",
            "pattern": WORD_PATTERN
        },
        "pos_id": {
            "type": "integer",
            "minimum": 1
        },
        "notes": {
            "type": ["string", 'null']
        },
        ATTRIBUTES: {
            "type": "array",
            "items": {
                "$ref": WORD_ATTRIBUTES_SCHEMA["$id"]
            }
        }
    }
}

WORD_UPDATE_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/word_update_payload.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for update word",
    "description": "Payload for update word",
    "type": "object",
    "required": [
        # no required properties.
    ],
    "additionalProperties": False,
    "properties": {
        "word": {
            # not required, but if present, we are making a spelling change
            "type": "string",
            "pattern": WORD_PATTERN
        },
        "notes": {
            "type": ["string", 'null']
        },
        ATTRIBUTES: {
            "type": "array",
            "items": {
                "$ref": WORD_ATTRIBUTES_SCHEMA["$id"]
            }
        }
    }
}

WORDLIST_PAYLOAD_SCHEMA = {
    # can be used for add or update of a list.
    "$id": "https://deutsch-lernen.doug/schemas/wordlist_payload.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for creating/updating wordlist",
    "description": "Payload for creating/updating wordlist",
    "required": [
        # haha, none are required.  string values must be at least 1 char if provided.
        # for creating a word list a name is of course required, but we will check that
        # in code, not here.
        #
        # we permit payloads with no name so that we can update a given list without having to specify a name.
        #
        # at most one of sqlcode/word_ids is permitted; can't specify both.
    ],
    "additionalProperties": False,
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "pattern": NAME_PATTERN
        },
        "citation": {
            "type": ["string", "null"],
            "pattern": STRING_PATTERN
        },
        "notes": {
            "type": ["string", 'null']
        },
        "sqlcode": {
            "type": ["string", "null"],
            "pattern": MULTILINE_STRING_PATTERN
        },
        "word_ids": {
            "type": "array",
            "items": {
                "type": "integer"
            }
        }
    },
    # this forces the mutual exclusivity of sqlcode and word_ids.
    "dependentSchemas": {
        "sqlcode": {
            "not": {"required": ["word_ids"]}
        },
        "word_ids": {
            "not": {"required": ["sqlcode"]}
        }
    }
}

# wordlist contents are notes and a list of word ids.

WORDLISTS_DELETE_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/wordlists_delete_payload.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "WORDLISTS_DELETE_PAYLOAD_SCHEMA",
    "description": "Payload for deleting multiple wordlists",
    "type": "array",
    "additionalProperties": False,
    "items": {
        "type": "integer"
    }
}

WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/wordlist_tag_add_delete_payload.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for add/delete tags",
    "description": """
    payload for adding/deleting multiple tags for a word in a wordlist.  word_id and
    wordlist_id must be in the url; they aren't here.
    """,
    "type": "array",
    "additionalProperties": False,
    "items": {
        "type": "string",
        "pattern": WORD_PATTERN
    }
}

##########################################################
#
#                   Responses
#
##########################################################

POS_STRUCTURE_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/pos_structure_response.json",
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
                            "attrvalue"
                        ],

                        "anyOf": [
                            # attrvalue has to be null if the word info is null.
                            {"$ref": "#/$attr_defs/attr_properties_null"},
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
                            "attrvalue"
                        ],

                        "anyOf": [
                            {"$ref": "#/$attr_defs/attr_properties"},
                        ]
                    }
                }
            }
        }
    },

    "$attr_defs": {
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
                }
            }
        },
        "attr_properties": {
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
                    "type": ["string", "null"]
                }
            }
        }
    }
}

QUIZ_ANSWER_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/quiz_answer_payload.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Quiz Data List",
    "description": "payload for posting a quiz answer",
    "type": "object",
    "required": [
        "quiz_id",
        "word_id",
        "attribute_id",
        "correct"
    ],
    "additionalProperties": False,
    "properties": {
        "quiz_id": {
            "type": "integer",
            "minimum": 1
        },
        "word_id": {
            "type": "integer",
            "minimum": 1
        },
        "correct": {
            "type": "boolean"
        },
        "attribute_id": {
            "type": "integer",
            "minimum": 1
        }
    }
}

QUIZ_REPORT_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/quiz_report_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Quiz Report",
    "description": """
    data for displaying quiz results for a wordlist.
    """,
    "type": "object",
    "required": [
        "quiz_key",
        "quiz_id",
        "wordlist_id",
        "scores"
    ],
    "properties": {
        "wordlist_id": {
            "type": "integer",
            "minimum": 1
        },
        "quiz_key": {
            "type": "string",
        },
        "quiz_id": {
            "type": "integer",
            "minimum": 1
        },
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "word",
                    "attrkey",
                    "word_id",
                    "presentation_count",
                    "correct_count",
                    "raw_score",
                    "last_presentation"
                ],
                "properties": {
                    "word": {
                        "type": "string",
                    },
                    "attrkey": {
                        "type": "string",
                    },
                    "word_id": {
                        "type": "integer",
                    },
                    # TODO: can we validate correct_count <= presentation_count?
                    "correct_count": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "presentation_count": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "raw_score": {
                        "type": "number",
                    },
                    "last_presentation": {
                        "type": "string"
                    }
                }
            }
        }
    }
}

QUIZ_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/quiz_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Quiz Data List",
    "description": "word attribute value to be quizzed",
    "type": "array",
    "items": {
        "required": [
            "quiz_id",
            "word_id",
            "attribute_id",
            "attrkey",
            "word",
            "attrvalue"
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
            "attribute_id": {
                "type": "integer",
                "minimum": 1
            },
            "word": {
                "type": "string"
            },
            "attrkey": {
                "type": "string"
            },
            "attrvalue": {
                "type": ["string", "null"]
            }
        }
    }
}

RELATION_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/relation_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Response for get relation",
    "description": """
    response for GET relation.
    
    note that the WORDLIST_WORD_SCHEMA has tags in it.  relations and tags have nothing to do with each other.
    oh well.  in a response that will simply not be populated.  it was either do it that way or replicate that
    structure here without the tags.
    """,
    "type": "object",
    "required": [
        "relation_id",
        "words",
        "notes",
        "description"
    ],
    "properties": {
        "relation_id": {
            "type": "integer",
            "minimum": 1,
        },
        "words": {
            "type": "array",
            "items": {
                "$ref": DISPLAYABLE_WORD_SCHEMA["$id"],
            }
        },
        "notes": {
            "type": ["string", 'null']
        },
        "description": {
            "type": ["string", 'null']
        }
    }
}

ARRAY_RELATION_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/array_relation_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Response for get relation",
    "description": """
    response for GET relation.
    """,
    "type": "array",
    "items": {
        "$ref": RELATION_RESPONSE_SCHEMA["$id"]
    }
}

WORD_TAG_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/word_tag_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": """
    list of tags for a wordlist_id/word_id
    """,
    "type": "object",
    "required": [
        # "word_id",   # not required
        "wordlist_id",
        "tags"
    ],
    "properties": {
        "wordlist_id": {
            "type": "integer",
        },
        "word_id": {
            "type": "integer",
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    }
}

WORDLIST_METADATA_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/wordlist_metadata_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist Metadata",
    "description": """
    wordlist metadata is all the info about a list except its contents.
    """,
    "type": "object",
    "required": [
        "wordlist_id",
        "name",
        "sqlcode",
        "citation",
        "list_type",
        "count",
    ],
    "properties": {
        "wordlist_id": {
            "type": "integer",
            "minimum": 1
        },
        "count": {
            "type": "integer"
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

ARRAY_WORDLIST_METADATA_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/array_wordlist_metadata_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Array of Wordlist Metadata Objects",
    "description": """
    response for GET relation.
    """,
    "type": "array",
    "items": {
        "$ref": WORDLIST_METADATA_RESPONSE_SCHEMA["$id"]
    }
}

WORDLIST_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/wordlist_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": """
    used for the response to GET /api/wordlist/<int:wordlist_id>, which is implemented in __get_wordlist().
    fully specifies a single word list.  defines the json documents that are returned when we do a get 
    request on a wordlist_id.  we get everything:
    - word list metadata
    - the notes
    - list type (smart, standard, empty)
    - all the words.
    note that we do not return the sqlcode if the list is a smart list.  we return the words fetched
    by the sql code.  which is the point of a smart list.
    """,
    "type": "object",
    "required": [
        "name",
        "wordlist_id",
        "list_type",
        "citation",
        "words",
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
        "words": {
            "type": "array",
            "items": {
                "$ref": DISPLAYABLE_WORD_SCHEMA["$id"],
            }
        }
    }
}

WORD_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/word_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Single Word Response",
    "description": """
    returned by api_word.get_word_by_id.
    """,
    "type": "object",
    "required": ["word", "word_id", "pos_name", "attributes", "notes"],
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
        "notes": {
            "type": ["string", "null"]
        },
        ATTRIBUTES: {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["attrkey", "sort_order", "attrvalue"],
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
                    }
                }
            }
        }
    }
}

ARRAY_WORD_RESPONSE_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/array_word_response.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Word",
    "description": "list of words with attributes",
    "type": "array",
    "items": {
        "$ref": WORD_RESPONSE_SCHEMA["$id"]
    }
}

WORD_WORDLIST_METADATA_MAP_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/word_wordlist_metadata_map.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Word to Wordlist Metadata Map",
    "description": """
    associates a word object with a wordlist metadata object.  this is used for api calls that find the wordlists
    that a word id is a member of.
    """,
    "type": "object",
    "required": [
        "word",
        "wordlist_metadata_list"
    ],
    "properties": {
        "word": {
            "$ref": WORD_RESPONSE_SCHEMA["$id"]
        },
        "wordlist_metadata_list": {
            "$ref": ARRAY_WORDLIST_METADATA_RESPONSE_SCHEMA["$id"]
        }
    }
}

ARRAY_WORD_WORDLIST_METADATA_MAP_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/array_word_wordlist_metadata_map.json",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Word",
    "description": "list of words with attributes",
    "type": "array",
    "items": {
        "$ref": WORD_WORDLIST_METADATA_MAP_SCHEMA["$id"]
    }
}

ALL_SCHEMAS = [
    RELATION_PAYLOAD_SCHEMA,
    WORD_ADD_PAYLOAD_SCHEMA,
    WORD_UPDATE_PAYLOAD_SCHEMA,
    WORDLISTS_DELETE_PAYLOAD_SCHEMA,
    WORDLIST_TAG_ADD_DELETE_PAYLOAD_SCHEMA,
    POS_STRUCTURE_RESPONSE_SCHEMA,
    QUIZ_ANSWER_PAYLOAD_SCHEMA,
    QUIZ_REPORT_RESPONSE_SCHEMA,
    QUIZ_RESPONSE_SCHEMA,
    RELATION_RESPONSE_SCHEMA,
    ARRAY_RELATION_RESPONSE_SCHEMA,
    WORD_TAG_RESPONSE_SCHEMA,
    WORDLIST_METADATA_RESPONSE_SCHEMA,
    ARRAY_WORDLIST_METADATA_RESPONSE_SCHEMA,
    WORDLIST_RESPONSE_SCHEMA,
    DISPLAYABLE_WORD_SCHEMA,
    WORD_ATTRIBUTES_SCHEMA,
    WORD_RESPONSE_SCHEMA,
    ARRAY_WORD_RESPONSE_SCHEMA,
    WORD_WORDLIST_METADATA_MAP_SCHEMA,
    ARRAY_WORD_WORDLIST_METADATA_MAP_SCHEMA,
    WORDLIST_PAYLOAD_SCHEMA
]

# build the registry ONCE at module level
registry = Registry().with_resources([
    (schema["$id"], Resource.from_contents(schema)) for schema in ALL_SCHEMAS
])


def get_validator(schema_dict):
    """Utility to get a validator with the pre-built registry."""
    from jsonschema.validators import validator_for
    cls = validator_for(schema_dict)
    return cls(schema_dict, registry=registry)
