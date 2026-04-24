"""Minimal JSON Schema validator used for local scaffolding tests.

Implements only the subset needed by this repository:
- type checks (object/array/string/integer/boolean)
- required
- enum
- minimum
- minLength
- properties
- items
- additionalProperties (boolean schema shortcut)
"""

from __future__ import annotations


class ValidationError(ValueError):
    pass


def validate(instance, schema):
    _validate(instance, schema, path='$')


def _validate(instance, schema, path):
    expected_type = schema.get('type')
    if expected_type:
        _check_type(instance, expected_type, path)

    required = schema.get('required', [])
    if isinstance(instance, dict):
        for key in required:
            if key not in instance:
                raise ValidationError(f"{path}: missing required key '{key}'")

    if 'enum' in schema and instance not in schema['enum']:
        raise ValidationError(f"{path}: value {instance!r} not in enum")

    if isinstance(instance, str) and 'minLength' in schema:
        if len(instance) < int(schema['minLength']):
            raise ValidationError(f"{path}: string shorter than minLength")

    if isinstance(instance, int) and 'minimum' in schema:
        if instance < int(schema['minimum']):
            raise ValidationError(f"{path}: integer below minimum")

    properties = schema.get('properties', {})
    if isinstance(instance, dict):
        for key, subschema in properties.items():
            if key in instance:
                _validate(instance[key], subschema, f"{path}.{key}")

        additional = schema.get('additionalProperties', None)
        if isinstance(additional, dict):
            for key, value in instance.items():
                if key not in properties:
                    _validate(value, additional, f"{path}.{key}")

    items = schema.get('items')
    if items and isinstance(instance, list):
        for idx, value in enumerate(instance):
            _validate(value, items, f"{path}[{idx}]")


def _check_type(instance, expected, path):
    mapping = {
        'object': dict,
        'array': list,
        'string': str,
        'integer': int,
        'boolean': bool,
    }
    py_type = mapping.get(expected)
    if py_type is None:
        return
    if not isinstance(instance, py_type):
        raise ValidationError(f"{path}: expected {expected}, got {type(instance).__name__}")
