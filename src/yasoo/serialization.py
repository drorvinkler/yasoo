import json
import warnings
from datetime import datetime
from enum import Enum
from inspect import signature
from typing import Dict, Any, Union, Mapping, Iterable, Callable, Type, Optional

from yasoo.default_customs import serialize_type, serialize_datetime
from yasoo.objects import DictWithSerializedKeys
from yasoo.utils import normalize_type, type_to_string

from .constants import ENUM_VALUE_KEY, ITERABLE_VALUE_KEY
from .utils import (
    resolve_types,
    get_fields,
    normalize_method,
    Field,
    is_obj_supported_primitive,
)


class Serializer:
    def __init__(self) -> None:
        super().__init__()
        self._custom_serializers: Dict[type, Callable[[Any], Dict[str, Any]]] = {
            datetime: serialize_datetime,
        }
        self._inheritance_serializers: Dict[type, Callable[[Any], Dict[str, Any]]] = {
            type: serialize_type,
        }

    def register(
        self, type_to_register: Optional[Type] = None, include_descendants: bool = False
    ):
        """
        Registers a custom serialization method that takes the object to be serialized and returns a json-serializable
        dictionary.

        :param type_to_register: The type of objects this method serializes. Can be a string, but then ``serialize``
            should be called with the ``globals`` parameter.
        :param include_descendants: Whether to use the registered method for objects inheriting from the given type
            or only for objects of the given type itself.
        """

        def registration_method(
            serialization_method: Union[Callable[[Any], Dict[str, Any]], staticmethod]
        ):
            method = normalize_method(serialization_method)
            t = type_to_register
            if t is None:
                t = next(iter(signature(method).parameters.values())).annotation
            self._custom_serializers[t] = method
            if include_descendants:
                self._inheritance_serializers[t] = method
            return serialization_method

        return registration_method

    def serialize(
        self,
        obj,
        type_key: Optional[str] = "__type",
        fully_qualified_types: bool = True,
        preserve_iterable_types: bool = False,
        stringify_dict_keys: bool = True,
        globals: Optional[Dict[str, Any]] = None,
    ) -> Optional[Union[bool, int, float, str, list, Dict[str, Any]]]:
        """
        Serializes an object to a json-serializable dictionary or list,
        or returns the object itself if it's json-serializable.

        :param obj: The object to serialize.
        :param type_key: The key in the resulting dictionary to contain the type name for non-primitive objects.
            Can be ``None`` to omit this key and rely on type hints when deserializing.
        :param fully_qualified_types: Whether to use fully qualified type names in the ``type_key``,
            i.e. whether to write "my_package.MyType" or just "MyType".
        :param preserve_iterable_types: Whether to serialize iterables as dictionaries with their type
            under ``type_key``, so they will be deserialized back to their type and not as a list.
        :param stringify_dict_keys: Whether to convert non-string dictionary keys to strings in a way that will
            allow deserializing them back to their original type. Useful for json.
        :param globals: If custom serialization methods were registered and used forward reference
            ('Foo' instead of Foo), this parameter should be a dictionary from type name to type, most easily
            acquired using the built-in ``globals()`` function.
        """
        if is_obj_supported_primitive(obj):
            return obj

        if globals:
            self._custom_serializers = resolve_types(self._custom_serializers, globals)

        result = self._serialize(
            obj,
            type_key,
            fully_qualified_types,
            preserve_iterable_types,
            stringify_dict_keys,
            inner=False,
        )
        result = _convert_to_json_serializable(result)
        return result

    def _serialize(
        self,
        obj,
        type_key,
        fully_qualified_types,
        preserve_iterable_types,
        stringify_dict_keys,
        inner=True,
    ):
        serialization_method = self._custom_serializers.get(type(obj))
        if serialization_method is None:
            for base_class, method in self._inheritance_serializers.items():
                if isinstance(obj, base_class):
                    serialization_method = method
                    break
        if serialization_method is not None:
            result = serialization_method(obj)
        else:
            try:
                result = self._serialize_data_class(
                    obj,
                    type_key,
                    fully_qualified_types,
                    preserve_iterable_types,
                    stringify_dict_keys,
                )
            except TypeError:
                if isinstance(obj, Enum):
                    result = {ENUM_VALUE_KEY: obj.value}
                elif isinstance(obj, Mapping):
                    result = self._serialize_mapping(
                        obj,
                        type_key,
                        fully_qualified_types,
                        preserve_iterable_types,
                        stringify_dict_keys,
                    )
                elif isinstance(obj, Iterable) and not isinstance(obj, str):
                    serialized = self._serialize_iterable(
                        obj,
                        type_key,
                        fully_qualified_types,
                        preserve_iterable_types,
                        stringify_dict_keys,
                    )
                    if isinstance(obj, list) or not preserve_iterable_types:
                        return serialized
                    result = {ITERABLE_VALUE_KEY: serialized}
                elif not inner:
                    raise
                else:
                    return obj

        if type_key is not None and type_key not in result:
            result[type_key] = self._get_type_data(obj, fully_qualified_types)
        return result

    def _serialize_data_class(
        self,
        obj,
        type_key,
        fully_qualified_types,
        preserve_iterable_types,
        stringify_dict_keys,
    ):
        fields = get_fields(type(obj))
        result = {
            f.name: self._serialize(
                getattr(obj, f.name),
                type_key,
                fully_qualified_types,
                preserve_iterable_types,
                stringify_dict_keys,
            )
            for f in fields
        }
        self._warn_for_possible_problems_in_deserialization(
            obj, fields, result, type_key is not None
        )
        return result

    def _serialize_iterable(
        self,
        obj: Iterable,
        type_key,
        fully_qualified_types,
        preserve_iterable_types,
        stringify_dict_keys,
    ):
        return [
            self._serialize(
                item,
                type_key,
                fully_qualified_types,
                preserve_iterable_types,
                stringify_dict_keys,
            )
            for item in obj
        ]

    def _serialize_mapping(
        self,
        obj: Mapping,
        type_key,
        fully_qualified_types,
        preserve_iterable_types,
        stringify_dict_keys,
    ):
        result = self._serialize_mapping_values(
            obj,
            type_key=type_key,
            fully_qualified_types=fully_qualified_types,
            preserve_iterable_types=preserve_iterable_types,
            stringify_dict_keys=stringify_dict_keys,
        )
        if any(not self._key_ok(k, stringify_dict_keys) for k in result.keys()):
            obj_type = self._get_type_data(obj, fully_qualified_types)
            d = self._serialize_complex_keys(
                result, obj_type, type_key, fully_qualified_types
            )
            result = self._serialize(
                d,
                type_key=type_key,
                fully_qualified_types=fully_qualified_types,
                preserve_iterable_types=preserve_iterable_types,
                stringify_dict_keys=stringify_dict_keys,
            )
        return result

    def _serialize_complex_keys(
        self, obj: dict, obj_type: str, type_key, fully_qualified_types
    ):
        def serialize_key(k):
            return json.dumps(
                self.serialize(
                    k,
                    type_key=type_key,
                    fully_qualified_types=fully_qualified_types,
                    preserve_iterable_types=True,
                )
            )

        try:
            data = {serialize_key(k): v for k, v in obj.items()}
            return DictWithSerializedKeys(data, obj_type)
        except TypeError:
            raise ValueError(
                f"Mapping {obj} contains a key which is not json-serializable and not yasoo-serializable"
            )

    def _serialize_mapping_values(
        self,
        obj,
        type_key,
        fully_qualified_types,
        preserve_iterable_types,
        stringify_dict_keys,
    ):
        return {
            k: self._serialize(
                v,
                type_key,
                fully_qualified_types,
                preserve_iterable_types,
                stringify_dict_keys,
            )
            for k, v in obj.items()
        }

    @classmethod
    def _key_ok(cls, key, stringify_dict_keys):
        return (
            isinstance(key, str)
            if stringify_dict_keys
            else is_obj_supported_primitive(key)
        )

    @classmethod
    def _warn_for_possible_problems_in_deserialization(
        cls, obj, fields: Iterable[Field], data: Dict[str, Any], type_key_present: bool,
    ) -> None:
        for f in fields:
            value = data[f.name]
            if not type_key_present:
                cls._check_for_unknown_dicts(f, value, obj.__class__.__name__)
            cls._check_for_unconvertables_or_invalid(
                obj, f, value, obj.__class__.__name__
            )

    @classmethod
    def _check_for_unknown_dicts(cls, f, value, obj_class_name):
        try:
            real_type, generic_args = normalize_type(f.field_type)
        except TypeError:
            real_type = generic_args = None

        if isinstance(value, list) and value:
            value = value[0]
            real_type = generic_args[0] if generic_args else None

        if not isinstance(value, dict):
            return

        if real_type is None:
            cls._warn(
                f'Field "{f.name}" in obj "{obj_class_name}" is a dict or an instance and has no type hint'
            )
        else:
            try:
                if not issubclass(real_type, Mapping) and not issubclass(
                    real_type, Iterable
                ):
                    get_fields(real_type)
            except TypeError:
                cls._warn(
                    f'Field "{f.name}" in obj "{obj_class_name}" is a dict or an instance but its type hint is an unsupported class. Make sure you register a deserializer'
                )

    @classmethod
    def _check_for_unconvertables_or_invalid(cls, obj, f, value, obj_class_name):
        if f.converter is not None and not isinstance(value, dict):
            try:
                value = f.converter(value)
            except:
                cls._warn(
                    f'Field "{f.name}" in obj "{obj_class_name}" has value {value} that could not be converted using its converter'
                )
                return

        if f.validator is not None and not isinstance(value, dict):
            try:
                f.validator(obj, f, value)
            except:
                cls._warn(
                    f'Field "{f.name}" in obj "{obj.__class__.__name__}" has value {value} that doesn\'t match this field\'s validator'
                )
                return

        if f.converter is not None:
            cls._warn(
                f'Field "{f.name}" in obj "{obj.__class__.__name__}" has a converter'
            )

    @staticmethod
    def _get_type_data(obj, fully_qualified_types) -> str:
        return type_to_string(type(obj), fully_qualified_types)

    @staticmethod
    def _warn(warning):
        warnings.warn(warning, RuntimeWarning, stacklevel=2)


def _convert_to_json_serializable(obj) -> Union[int, float, str, list, dict, None]:
    if is_obj_supported_primitive(obj):
        return obj
    if isinstance(obj, Mapping):
        return {key: _convert_to_json_serializable(value) for key, value in obj.items()}
    if isinstance(obj, Iterable):
        return [_convert_to_json_serializable(item) for item in obj]
    raise TypeError(
        f'Found object of type "{type(obj).__name__}" which cannot be serialized'
    )
