import unittest
from dlernen.decorators import js_validate_result
from dlernen.dlernen_json_schema import WORD_RESPONSE_SCHEMA, WORD_ADD_PAYLOAD_SCHEMA, ATTRIBUTES
import jsonschema

VALID_PAYLOAD = {
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
}

INVALID_PAYLOAD = "this is some bullshit right here"

VALID_RESPONSE = {
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
}

INVALID_RESPONSE = INVALID_PAYLOAD


def nothing_out():
    return None


def valid_out():
    return VALID_RESPONSE


def garbage_out():
    return INVALID_RESPONSE


@js_validate_result(WORD_RESPONSE_SCHEMA)
def decorated_nothing_out():
    return None


@js_validate_result(WORD_RESPONSE_SCHEMA)
def decorated_valid_out():
    return VALID_RESPONSE


@js_validate_result(WORD_RESPONSE_SCHEMA)
def decorated_garbage_out():
    return INVALID_RESPONSE


class ResultDecoratorTests(unittest.TestCase):
    def test_functools(self):
        # decorated function should have its original name
        decorator = js_validate_result(WORD_RESPONSE_SCHEMA)
        decorated_function = decorator(valid_out)

        self.assertEqual(valid_out.__name__, decorated_function.__name__)

    def test_nothing_out(self):
        decorator = js_validate_result(WORD_RESPONSE_SCHEMA)
        wrapper = decorator(valid_out)
        wrapper()

    def test_valid_out(self):
        decorator = js_validate_result(WORD_RESPONSE_SCHEMA)
        wrapper = decorator(valid_out)
        wrapper()

    def test_garbage_out(self):
        decorator = js_validate_result(WORD_RESPONSE_SCHEMA)
        wrapper = decorator(garbage_out)
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            wrapper()

    def test_decorated_nothing_out(self):
        decorated_valid_out()

    def test_decorated_valid_out(self):
        decorated_valid_out()

    def test_decorated_garbage_out(self):
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            decorated_garbage_out()

