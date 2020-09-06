import json
from enum import Enum
from importlib import import_module
from inspect import signature
from itertools import zip_longest
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
    List,
    Tuple,
    overload,
)

from .constants import ENUM_VALUE_KEY, ITERABLE_VALUE_KEY
from .objects import DictWithSerializedKeys
from .utils import (
    resolve_types,
    get_fields,
    normalize_method,
    normalize_type,
    is_obj_supported_primitive,
    SUPPORTED_PRIMITIVES,
)

T = TypeVar("T")
NoneType = type(None)


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

    @overload
    def deserialize(
        self,
        data: Optional[Union[bool, int, float, str, list, Dict[str, Any]]],
        obj_type: Callable[[], T],
        type_key: Optional[str] = "__type",
        globals: Optional[Dict[str, Any]] = None,
    ) -> T:
        ...

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
        :param globals: A dictionary from type name to type, most easily acquired using the built-in ``globals()``
            function.
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
        external_globals: Dict[str, Any],
    ):
        all_globals = dict(globals())
        all_globals.update(external_globals)
        if is_obj_supported_primitive(data):
            return data
        if isinstance(data, list):
            list_types = self._get_list_types(obj_type, data)
            return [
                self._deserialize(d, t, type_key, all_globals) for t, d in list_types
            ]

        obj_type = self._get_object_type(obj_type, data, type_key, all_globals)
        if type_key in data:
            data.pop(type_key)

        deserialization_method = self._custom_deserializers.get(obj_type)
        if deserialization_method:
            return deserialization_method(data)

        key_type = None
        try:
            fields = {f.name: f for f in get_fields(obj_type)}
        except TypeError:
            real_type, generic_args = normalize_type(obj_type)
            if issubclass(real_type, Enum):
                return obj_type(data[ENUM_VALUE_KEY])
            elif issubclass(real_type, Mapping):
                key_type = generic_args[0] if generic_args else None
                if (
                    key_type
                    and key_type not in SUPPORTED_PRIMITIVES
                    and key_type is not NoneType
                ):
                    obj_type = DictWithSerializedKeys
                    fields = {f.name: f for f in get_fields(obj_type)}
                    value_type = generic_args[1] if generic_args else Any
                    fields["data"].field_type = Dict[str, value_type]
                else:
                    return self._load_mapping(
                        data, real_type, generic_args, type_key, all_globals
                    )
            elif issubclass(real_type, Iterable):
                # If we got here it means data is not a list, so obj_type came from the data itself and is safe to use
                return self._load_iterable(data, obj_type, type_key, all_globals)
            else:
                raise

        self._check_for_missing_fields(data, fields, obj_type)
        self._check_for_extraneous_fields(data, fields, obj_type)
        self._load_inner_fields(data, fields, type_key, all_globals)
        if obj_type is DictWithSerializedKeys:
            return self._load_dict_with_serialized_keys(
                obj_type(**data), key_type, type_key, all_globals
            )
        return obj_type(**data)

    def _load_dict_with_serialized_keys(
        self, obj: DictWithSerializedKeys, key_type, type_key, all_globals
    ):
        data = {
            self._deserialize(json.loads(k), key_type, type_key, all_globals): v
            for k, v in obj.data.items()
        }
        obj_type = Deserializer._get_type(obj.original_type, all_globals)
        return obj_type(data)

    def _load_mapping(
        self, data: Mapping, obj_type, generic_args, type_key, all_globals
    ):
        val_type = generic_args[1] if len(generic_args) > 1 else None
        return obj_type(
            {
                k: self._deserialize(v, val_type, type_key, all_globals)
                for k, v in data.items()
            }
        )

    def _load_iterable(self, data, obj_type, type_key, all_globals):
        return obj_type(
            self._deserialize(i, None, type_key, all_globals)
            for i in data[ITERABLE_VALUE_KEY]
        )

    def _load_inner_fields(self, data, fields, type_key, all_globals):
        for key, value in data.items():
            field = fields[key]
            data[key] = self._deserialize(
                value, field.field_type, type_key, all_globals
            )

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
    def _get_list_types(
        type_hint: Optional[type], data: list
    ) -> List[Tuple[Optional[type], Any]]:
        if type_hint is None:
            return [(None, item) for item in data]
        _, generic_args = normalize_type(type_hint)
        if len(generic_args) == 1 or len(generic_args) == 2 and generic_args[1] is ...:
            return [(generic_args[0], item) for item in data]
        if len(generic_args) == len(data):
            return list(zip(generic_args, data))
        return list(zip_longest(generic_args, data))

    @staticmethod
    def _get_object_type(
        obj_type: Optional[Type[T]],
        data: Dict[str, Any],
        type_key: str,
        all_globals: Dict[str, Any],
    ) -> Type:
        if type_key in data:
            return Deserializer._get_type(data[type_key], all_globals)
        if obj_type is None:
            raise ValueError(
                f"type key not found in data and obj type could not be inferred.\nData: {json.dumps(data)}"
            )
        return obj_type

    @staticmethod
    def _get_type(type_name: str, all_globals: Dict[str, Any]) -> Type:
        if "." not in type_name:
            return Deserializer._get_non_fully_qualified_type(type_name, all_globals)
        return Deserializer._get_fully_qualified_type(type_name)

    @staticmethod
    def _get_non_fully_qualified_type(
        type_name: str, all_globals: Dict[str, Any]
    ) -> Type:
        if type_name == "list":
            return list
        if type_name == "set":
            return set
        if type_name == "tuple":
            return tuple
        if type_name == "dict":
            return dict
        if type_name not in all_globals:
            raise ValueError(f"type {type_name} not found in globals.")
        return all_globals[type_name]

    @staticmethod
    def _get_fully_qualified_type(type_name):
        module_name = type_name[: type_name.rindex(".")]
        class_name = type_name[len(module_name) + 1 :]
        return getattr(import_module(module_name), class_name)
