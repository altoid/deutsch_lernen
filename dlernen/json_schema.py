import jsonschema

WORDLIST_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Wordlist",
    "description": "wordlist and basic properties, optionally with word_ids",
    "type": "object",
    "properties": {
        # name
        # list_id
        # count
        # whether it is a spart playlist
        # optional:  list of word ids.
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
    "required": ["name", "wordlist_id", "count", "is_smart"]
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
        # whether it is a spart playlist
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
            "type": "string",
            "minLength": 1
        },
        "source_is_url": {
            "type": "boolean"
        },
        "known_words": {
            "type": "array",
            "items": {
                "type": "object",
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


WORD_SCHEMA = {
    "$schema": jsonschema.Draft202012Validator.META_SCHEMA["$id"],
    "title": "Word",
    "description": "word with attributes",
    "type": "object",
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

        "article": {
            "type": ["string", "null"]
        },
        "definition": {
            "type": ["string", "null"]
        },
        "first_person_plural": {
            "type": ["string", "null"]
        },
        "first_person_singular": {
            "type": ["string", "null"]
        },
        "past_participle": {
            "type": ["string", "null"]
        },
        "plural": {
            "type": ["string", "null"]
        },
        "second_person_plural": {
            "type": ["string", "null"]
        },
        "second_person_singular": {
            "type": ["string", "null"]
        },
        "third_person_past": {
            "type": ["string", "null"]
        },
        "third_person_plural": {
            "type": ["string", "null"]
        },
        "third_person_singular": {
            "type": ["string", "null"]
        }
    },
    "required": ["word", "word_id", "pos_name"]
    # the attributes - article, definition, etc. - are all optional.
}
