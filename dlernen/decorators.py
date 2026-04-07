import functools
from dlernen.dlernen_json_schema import get_validator


def js_validate_result(schema):
    def decorator_js_validate_result(func):
        @functools.wraps(func)
        def wrapper_js_validate_result(*args, **kwargs):
            result = func(*args, **kwargs)
            # NB do not check for None or empty results.  trivial return values should pass validation.
            get_validator(schema).validate(result)
            return result
        return wrapper_js_validate_result
    return decorator_js_validate_result


# validate payloads and results with different decorators
