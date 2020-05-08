import json
from enum import Enum
from importlib import import_module
from inspect import signature
from typing import (
    Optional,
    Type,
    Union,
    Callable,
    Dict,
    Any,
    TypeVar,
    Mapping,
    Iterable,
)

from .constants import ENUM_VALUE_KEY, ITERABLE_VALUE_KEY
from .utils import (
    resolve_types,
    get_fields,
    normalize_method,
    normalize_type,
    is_obj_supported_primitive,
)

T = TypeVar("T")


class Deserializer:
    def __init__(self) -> None:
        super().__init__()
        self._custom_deserializers: Dict[Type[T], Callable[[Dict[str, Any]], T]] = {}

    def register(self, type_to_register: Optional[Union[Type, str]] = None):
        """
        Registers a custom deserialization method that takes a dictionary and returns an instance of the registered
        type.

        :param type_to_register: The type of objects this method deserializes to. Can be a string, but then
            ``deserialize`` should be called with the ``globals`` parameter.
        """

        def registration_method(
            deserialization_method: Union[Callable[[Dict[str, Any]], Any], staticmethod]
        ):
            method = normalize_method(deserialization_method)
            t = type_to_register
            if t is None:
                t = signature(method).return_annotation
            self._custom_deserializers[t] = method
            return deserialization_method

        return registration_method

    def deserialize(
        self,
        data: Optional[Union[bool, int, float, str, list, Dict[str, Any]]],
        obj_type: Optional[Type[T]] = None,
        type_key: Optional[str] = "__type",
        globals: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Deserializes an object from a dictionary or a list of dictionaries,
        or returns the object itself if it's a primitive (including ``None``).

        :param data: The dictionary.
        :param obj_type: The type of the object to deserialize. Can only be ``None`` if ``data`` contains a type key.
        :param type_key: The key in ``data`` that contains the type name for non-primitive objects.
            Can be ``None`` if this key was omitted during serialization and deserialization should rely on type hints.
        :param globals: If custom deserialization methods were registered and used forward reference
            ('Foo' instead of Foo), this parameter should be a dictionary from type name to type, most easily
            acquired using the built-in ``globals()`` function.
        """
        if globals:
            self._custom_deserializers = resolve_types(
                self._custom_deserializers, globals
            )

        return self._deserialize(data, obj_type, type_key, globals or {})

    def _deserialize(
        self,
        data: Optional[Union[bool, int, float, str, list, Dict[str, Any]]],
        obj_type: Optional[Type[T]],
        type_key: Optional[str],
        globals: Dict[str, Any],
    ):
        if is_obj_supported_primitive(data):
            return data
        if isinstance(data, list):
            if obj_type is not None:
                _, generic_args = normalize_type(obj_type)
                obj_type = generic_args[0] if generic_args else None
            return [self._deserialize(d, obj_type, type_key, globals) for d in data]

        obj_type = self._get_object_type(obj_type, data, type_key, globals)
        if type_key in data:
            data.pop(type_key)

        deserialization_method = self._custom_deserializers.get(obj_type)
        if deserialization_method:
            return deserialization_method(data)

        try:
            fields = {f.name: f for f in get_fields(obj_type)}
        except TypeError:
            real_type, generic_args = normalize_type(obj_type)
            if issubclass(real_type, Enum):
                return obj_type(data[ENUM_VALUE_KEY])
            if issubclass(real_type, Mapping):
                return self._load_mapping(
                    data, real_type, generic_args, type_key, globals
                )
            if issubclass(real_type, Iterable):
                # If we got here this means data is not a list, so obj_type came from the data itself and is safe to use
                return self._load_iterable(data, obj_type, type_key, globals)
            raise

        self._check_for_missing_fields(data, fields, obj_type)
        self._check_for_extraneous_fields(data, fields, obj_type)
        self._load_inner_fields(data, fields, type_key, globals)
        return obj_type(**data)

    def _load_mapping(self, data: Mapping, obj_type, generic_args, type_key, globals):
        val_type = generic_args[1] if len(generic_args) > 1 else None
        return obj_type(
            {
                k: self._deserialize(v, val_type, type_key, globals)
                for k, v in data.items()
            }
        )

    def _load_iterable(self, data, obj_type, type_key, globals):
        return obj_type(
            self._deserialize(i, None, type_key, globals)
            for i in data[ITERABLE_VALUE_KEY]
        )

    def _load_inner_fields(self, data, fields, type_key, globals):
        for key, value in data.items():
            field = fields[key]
            data[key] = self._deserialize(value, field.field_type, type_key, globals)

    @staticmethod
    def _check_for_missing_fields(data, fields, obj_type):
        missing = {
            name
            for name, field in fields.items()
            if name not in data and field.mandatory
        }
        if missing:
            missing_str = '", "'.join(missing)
            raise ValueError(
                f'Missing fields "{missing_str}" for object type "{obj_type.__name__}". Data is:\n{json.dumps(data)}'
            )

    @staticmethod
    def _check_for_extraneous_fields(data, fields, obj_type):
        extraneous = set(data.keys()).difference(fields)
        if extraneous:
            extraneous_str = '", "'.join(extraneous)
            raise ValueError(
                f'Found extraneous fields "{extraneous_str}" for object type "{obj_type.__name__}". Data is:\n{json.dumps(data)}'
            )

    @staticmethod
    def _get_object_type(
        obj_type: Optional[Type[T]],
        data: Dict[str, Any],
        type_key: str,
        globals: Dict[str, Any],
    ) -> Type:
        if type_key in data:
            return Deserializer._get_type(data[type_key], globals)
        if obj_type is None:
            raise ValueError(
                f"type key not found in data and obj type could not be inferred.\nData: {json.dumps(data)}"
            )
        return obj_type

    @staticmethod
    def _get_type(type_name: str, globals: Dict[str, Any]) -> Type:
        if "." not in type_name:
            return Deserializer._get_non_fully_qualified_type(type_name, globals)
        return Deserializer._get_fully_qualified_type(type_name)

    @staticmethod
    def _get_non_fully_qualified_type(type_name: str, globals: Dict[str, Any]) -> Type:
        if type_name == "list":
            return list
        if type_name == "set":
            return set
        if type_name == "tuple":
            return tuple
        if type_name == "dict":
            return dict
        if type_name not in globals:
            raise ValueError(f"type {type_name} not found in globals.")
        return globals[type_name]

    @staticmethod
    def _get_fully_qualified_type(type_name):
        module_name = type_name[: type_name.rindex(".")]
        class_name = type_name[len(module_name) + 1 :]
        return getattr(import_module(module_name), class_name)
