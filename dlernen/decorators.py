import functools
from dlernen.dlernen_json_schema import get_validator


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


# validate payloads and results with different decorators
