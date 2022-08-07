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
        "attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "minLength": 1,
                    },
                    "value": {
                        "type": "string"
                    }
                },
                "required": ["key", "value"]
            }
        }
    },
    "required": ["word", "word_id", "pos_name", "attributes"]
}
