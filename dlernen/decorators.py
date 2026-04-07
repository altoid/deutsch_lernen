import functools
from dlernen.dlernen_json_schema import get_validator
from flask import request
import jsonschema

# this decorator can throw an exception (validation error).  for that reason we should not decorate endpoints with
# this.  this should be used to decorate functions called by the endpoint.  those functions should then be called
# from within the try/except block in the endpoint.


def js_validate_result(schema):
    def decorator_js_validate_result(func):
        @functools.wraps(func)
        def wrapper_js_validate_result(*args, **kwargs):
            result = func(*args, **kwargs)
            if result is not None:
                get_validator(schema).validate(result)
            return result
        return wrapper_js_validate_result
    return decorator_js_validate_result


# this decorator also can throw a validation error, but it must be used to decorate endpoints.
# FIXME - no unit tests for this until i figure out how to fake the flask request object.
def js_validate_payload(schema):
    def decorator_js_validate_payload(func):
        @functools.wraps(func)
        def wrapper_js_validate_payload(*args, **kwargs):
            try:
                payload = request.get_json()
                get_validator(schema).validate(payload)
            except jsonschema.ValidationError as e:
                return "bad payload: %s" % e.message, 400

            return func(*args, **kwargs)
        return wrapper_js_validate_payload
    return decorator_js_validate_payload
