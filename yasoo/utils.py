from typing import Dict, Any, Union, Type, List, Optional

import attr
from attr.exceptions import NotAnAttrsClassError

try:
    import dataclasses
except ModuleNotFoundError:
    dataclasses = None


@attr.attrs
class Field:
    name: str = attr.attrib()
    field_type: Type = attr.attrib()
    mandatory: bool = attr.attrib()
    validator: Optional[callable] = attr.attrib(default=None)
    converter: Optional[callable] = attr.attrib(default=None)


def resolve_types(
    to_resolve: Dict[Union[Type, str], Any], globals: Dict[str, Any]
) -> Dict[Type, Any]:
    return {_resolve_type(globals, k): v for k, v in to_resolve.items()}


def get_fields(obj_type: Type) -> List[Field]:
    try:
        return [
            Field(f.name, f.type, f.default == attr.NOTHING, f.validator, f.converter)
            for f in attr.fields(obj_type)
        ]
    except NotAnAttrsClassError:
        try:
            return [
                Field(f.name, f.type, _dataclass_field_mandatory(f))
                for f in dataclasses.fields(obj_type)
            ]
        except (TypeError, AttributeError):
            pass
    raise TypeError("can only serialize attrs or dataclass classes")


def normalize_method(method) -> callable:
    return method.__func__ if isinstance(method, staticmethod) else method


def is_obj_supported_primitive(obj):
    return (
        isinstance(obj, bool)
        or isinstance(obj, int)
        or isinstance(obj, float)
        or isinstance(obj, str)
        or obj is None
    )


def _resolve_type(globals, t):
    return globals.get(t) if isinstance(t, str) else t


def _dataclass_field_mandatory(field):
    return (
        field.default == dataclasses.MISSING
        and field.default_factory == dataclasses.MISSING
    )
