import jsonschema

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

ADDWORD_PAYLOAD_SCHEMA = {
    "$id": "https://deutsch-lernen.doug/schemas/addword_payload",
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Payload for add word",
    "description": "Payload for add word",
    "type": "object",
    "required": [
        "word",
        "pos_name",
        "attributes"
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
        # "word" not required for update
        "attributes"
    ],
    "properties": {
        "word": {
            # this is optional
            "type": "string",
            "minLength": 1
        },
        "attributes": {
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
    "properties": {
        "word_ids": {
            "type": "array",
            "items": {
                "type": "integer"
            }
        }
    }
}

WORDLISTS_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": "wordlist and basic properties",
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            # name
            # list_id
            # count
            # whether it is a smart word list
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
            "is_smart": {
                "type": "boolean"
            }
        },
        "required": [
            "name",
            "wordlist_id",
            "count",
            "is_smart"
        ]
    }
}

WORDLIST_ATTRIBUTE_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": "wordlist and basic properties, optionally with word_ids",
    "type": "object",
    "required": [
        "id",
        "name",
        "code",
        "source"
    ],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1
        },
        "code": {
            "type": "string",
            "minLength": 0
        },
        "source": {
            "type": "string",
            "minLength": 0
        },
        "id": {
            "type": "integer",
            "minimum": 1
        }
    }
}

WORDLIST_DETAIL_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": "wordlist and basic properties, optionally with word_ids",
    "type": "object",
    "properties": {
        # name
        # list_id
        # count
        # whether it is a smart word list
        # optional:  list of word ids.
        "name": {
            "type": "string",
            "minLength": 1
        },
        "wordlist_id": {
            "type": "integer",
            "minimum": 1
        },
        "is_smart": {
            "type": "boolean"
        },
        "source": {
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
                        "type": "string"
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
    "required": ["name", "wordlist_id", "is_smart", "source", "known_words", "unknown_words",
                 "notes", "source_is_url"]
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
