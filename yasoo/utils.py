import dataclasses
from typing import Dict, Any, Union, Type, List

import attr
from attr.exceptions import NotAnAttrsClassError


@dataclasses.dataclass
class Field:
    name: str
    field_type: Type
    mandatory: bool


def resolve_types(to_resolve: Dict[Union[Type, str], Any], globals: Dict[str, Any]) -> Dict[Type, Any]:
    return {globals.get(k) if isinstance(k, str) else k: v for k, v in to_resolve.items()}


def get_fields(obj_type: Type) -> List[Field]:
    try:
        return [Field(f.name, f.type, f.default == attr.NOTHING) for f in attr.fields(obj_type)]
    except NotAnAttrsClassError:
        try:
            return [Field(f.name, f.type, f.default == dataclasses.MISSING and f.default_factory == dataclasses.MISSING)
                    for f in dataclasses.fields(obj_type)]
        except TypeError:
            raise TypeError('can only serialize attrs or dataclass classes')


def normalize_method(method) -> callable:
    return method.__func__ if isinstance(method, staticmethod) else method
