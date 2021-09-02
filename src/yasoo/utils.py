from functools import lru_cache
from importlib import import_module
from typing import Dict, Any, Union, List, Optional, Tuple

import attr
from attr.exceptions import NotAnAttrsClassError

try:
    import dataclasses
except ModuleNotFoundError:
    dataclasses = None

try:
    # Python 3.6
    from typing import GenericMeta as GenericType

    def _get_origin(t: GenericType):
        return t.__extra__ or t.__origin__

    def _is_optional(t: type):
        return (
            getattr(t, "__origin__", None) is Union
            and len(t.__args__) == 2
            and any(a is NoneType for a in t.__args__)
        )


except ImportError:
    # Python >=3.7
    from typing import _GenericAlias as GenericType

    def _get_origin(t: GenericType):
        return t.__origin__

    def _is_optional(t: type):
        return (
            isinstance(t, GenericType)
            and _get_origin(t) is Union
            and len(t.__args__) == 2
            and any(a is NoneType for a in t.__args__)
        )


generic_types = (GenericType,)

try:
    # Python >= 3.9
    from types import GenericAlias

    generic_types += (GenericAlias,)
except ImportError:
    pass


NoneType = type(None)
SUPPORTED_PRIMITIVES = {bool, int, float, str}
_SUPPORTED_PRIMITIVES = tuple(SUPPORTED_PRIMITIVES)


@attr.attrs
class Field:
    name: str = attr.attrib()
    field_type: type = attr.attrib()
    mandatory: bool = attr.attrib()
    validator: Optional[callable] = attr.attrib(default=None)
    converter: Optional[callable] = attr.attrib(default=None)


def resolve_types(
    to_resolve: Dict[Union[type, str], Any], globals: Dict[str, Any]
) -> Dict[type, Any]:
    return {_resolve_type(globals, k): v for k, v in to_resolve.items()}


@lru_cache(None)
def get_fields(obj_type: type) -> List[Field]:
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


@lru_cache(None)
def normalize_type(t: Union[type, GenericType]) -> Tuple[type, tuple]:
    if t == Any:
        t = None
    if _is_optional(t):
        return normalize_type(next(a for a in t.__args__ if a is not NoneType))
    if isinstance(t, generic_types):
        real_type = _get_origin(t)
        generic_args = t.__args__
    elif t is None or isinstance(t, type):
        real_type = t
        generic_args = tuple()
    else:
        raise TypeError(
            f"Found type annotation {t}, which is not a type and not a generic."
        )
    return real_type, generic_args


def is_obj_supported_primitive(obj):
    return isinstance(obj, _SUPPORTED_PRIMITIVES) or obj is None


@lru_cache(None)
def type_to_string(t: type, fully_qualified: bool) -> str:
    name = t.__name__
    if fully_qualified:
        return ".".join((t.__module__, name))
    else:
        return name


@lru_cache(None)
def fully_qualified_string_to_type(fully_qualified_type_name: str) -> type:
    module_name = fully_qualified_type_name[: fully_qualified_type_name.rindex(".")]
    class_name = fully_qualified_type_name[len(module_name) + 1 :]
    return getattr(import_module(module_name), class_name)


def _resolve_type(globals, t):
    return globals.get(t) if isinstance(t, str) else t


def _dataclass_field_mandatory(field):
    return (
        field.default == dataclasses.MISSING
        and field.default_factory == dataclasses.MISSING
    )
