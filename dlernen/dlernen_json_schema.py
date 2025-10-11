import jsonschema

# without checking for \r and \n this will not match multiline strings.
STRING_PATTERN = r"""^\S((.|[\r\n])*\S)*$"""

ADDATTRIBUTES_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/addattributes_payload",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for add attributes",
    "description": "Payload for add attributes",
    "type": "object",
    "required": [
        "attributes"
    ],
    "properties": {
        "attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "attrkey",
                    "attrvalue"
                ],
                "properties": {
                    "attrkey": {
                        "type": "string",
                        "minLength": 1
                    },
                    "attrvalue": {
                        "type": "string",
                        "minLength": 1
                    }
                }
            }
        }
    }
}

REFRESH_WORDLISTS_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/refresh_wordlists",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload refreshing wordlists",
    "description": "Used for implementing POST to /api/wordlists",
    "type": "object",
    "required": [
        "word",
        "word_id"
    ],
    "properties": {
        "word": {
            "type": "string",
            "minLength": 1
        },
        "word_id": {
            "type": "integer",
            "minimum": 1
        }
    }
}

ADDWORD_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/addword_payload",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for add word",
    "description": "Payload for add word",
    "type": "object",
    "required": [
        "word",
        "pos_name"
    ],
    "properties": {
        "word": {
            "type": "string",
            "minLength": 1
        },
        "pos_name": {
            "type": "string",
            "minLength": 1
        },
        "attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "attrkey",
                    "attrvalue"
                ],
                "properties": {
                    "attrkey": {
                        "type": "string",
                        "minLength": 1
                    },
                    "attrvalue": {
                        "type": "string",
                        "minLength": 1
                    }
                }
            }
        }
    }
}

UPDATEWORD_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/updateword_payload",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for update word",
    "description": "Payload for update word",
    "type": "object",
    "required": [
        # no required fields
    ],
    "properties": {
        "word": {
            # this is optional
            "type": "string",
            "minLength": 1
        },
        "attributes_adding": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "attrvalue",
                    "attrkey"
                ],
                "properties": {
                    "attrkey": {
                        "type": "string",
                        "minimum": 1
                    },
                    "attrvalue": {
                        "type": "string",
                        "minLength": 1
                    }
                }
            }
        },
        "attributes_deleting": {
            "type": "array",
            "items": {
                "type": "integer",
                "minimum": 1
            }
        },
        "attributes_updating": {
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
                        "minLength": 1
                    }
                }
            }
        }
    }
}

WORD_METADATA_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/word_metadata",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Quiz Data List",
    "description": "list of quiz query results",
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "tag",
            "pos_name",
            "pos_fields"
        ],
        "properties": {
            "tag": {
                "type": "string",
                "minLength": 1
            },
            "pos_name": {
                "type": "string",
                "minLength": 1
            },
            "pos_fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "attrkey",
                        "field_key",
                        "sort_order"
                    ],
                    "properties": {
                        "attrkey": {
                            "type": "string",
                            "minLength": 1
                        },
                        "attrvalue": {
                            "type": "string",
                            "minLength": 1
                        },
                        "fieldkey": {
                            "type": "string",
                            "minLength": 1
                        },
                        "sort_order": {
                            "type": "integer",
                            "minimum": 0
                        }
                    }
                }
            }
        }
    }
}

QUIZ_DATA_SCHEMA = {
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
                "type": "string",
                "minLength": 1
            },
            "word": {
                "type": "string",
                "minLength": 1
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
                    "type": "string",
                    "minLength": 1
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

WORDIDS_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "WordIDList",
    "description": "list of word ids",
    "type": "object",
    "required": [
        "word_ids",
        "attribute_id"
    ],
    "properties": {
        "word_ids": {
            "type": "array",
            "items": {
                "type": "integer"
            }
        },
        "attribute_id": {
            "type": "integer",
            "minimum": 1
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
                "type": "string",
                "minLength": 1
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

# TODO - revise this to have 'words_added', 'words_removed' and wordids_removed keywords, to replace 'words' keyword.
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
        # FIXME this schema is used for both creating and updating a word list.
        # we permit payloads with no name so that we can update a given list without having to specify a name.
    ],
    "properties": {
        "name": {
            "type": "string",
            "pattern": STRING_PATTERN
        },
        "citation": {
            "type": ["string", "null"]
        },
        "notes": {
            "type": "string",
            "minLength": 1
        },
        "sqlcode": {
            "type": ["string", "null"],
            "pattern": STRING_PATTERN
        },
        "words": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1
            }
        }
    }
}

# TODO - citation and sqlcode should be nonempty strings or null.  we should be able to store and retrieve null
#   values for these.
WORDLIST_METADATA_RESPONSE_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": "wordlist and basic properties, optionally with word_ids",
    "type": "object",
    "required": [
        "wordlist_id",
        "name",
        "sqlcode",
        "citation"
    ],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1
        },
        "sqlcode": {
            "type": ["string", "null"],
            "pattern": STRING_PATTERN
        },
        "citation": {
            "type": ["string", "null"]
        },
        "wordlist_id": {
            "type": "integer",
            "minimum": 1
        }
    }
}

WORDLIST_RESPONSE_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": """
    used for the response to GET /api/wordlist/<int:wordlist_id>, which is implemented in get_wordlist().
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
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1
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
                "empty" # no code or words
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
                        "type": "string",
                        "minLength": 1
                    },
                    "word_id": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "article": {
                        "type": ["string", "null"],
                        "minLength": 1
                    },
                    "definition": {
                        "type": "string",
                        "minLength": 1
                    }
                }
            }
        },
        "unknown_words": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1
            }
        }
    },
    "required": [
        "name",
        "wordlist_id",
        "list_type",
        "citation",
        "known_words",
        "unknown_words",
        "notes",
        "source_is_url"
    ]
}

WORDS_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Word",
    "description": "list of words with attributes",
    "type": "array",
    "items": {
        "type": "object",
        "required": ["word", "word_id", "pos_name", "attributes"],
        "properties": {
            "word": {
                "type": "string",
                "minLength": 1
            },
            "word_id": {
                "type": "integer",
                "minimum": 1
            },
            "pos_name": {
                "type": "string",
                "minLength": 1
            },
            "attributes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["attrkey", "sort_order", "attrvalue", "attrvalue_id"],
                    "properties": {
                        "attrkey": {
                            "type": "string",
                            "minLength": 1
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
