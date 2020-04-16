import logging
from enum import Enum
from inspect import signature
from typing import Dict, Any, Union, Mapping, Iterable, Callable, Type, Optional

from .constants import ENUM_VALUE_KEY, ITERABLE_VALUE_KEY
from .utils import (
    resolve_types,
    get_fields,
    normalize_method,
    Field,
    is_obj_supported_primitive,
)

_logger = logging.getLogger(__name__)


class Serializer:
    def __init__(self) -> None:
        super().__init__()
        self._custom_serializers = {}

    def register(self, type_to_register: Optional[Type] = None):
        """
        Registers a custom serialization method that takes the object to be serialized and returns a json-serializable
        dictionary.

        :param type_to_register: The type of objects this method serializes. Can be a string, but then ``serialize``
            should be called with the ``globals`` parameter.
        """

        def registration_method(
            serialization_method: Union[Callable[[Any], Dict[str, Any]], staticmethod]
        ):
            method = normalize_method(serialization_method)
            t = type_to_register
            if t is None:
                t = next(iter(signature(method).parameters.values())).annotation
            self._custom_serializers[t] = method
            return serialization_method

        return registration_method

    def serialize(
        self,
        obj,
        type_key: Optional[str] = "__type",
        fully_qualified_types: bool = True,
        preserve_iterable_types: bool = False,
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
        :param globals: If custom serialization methods were registered and used forward reference
            ('Foo' instead of Foo), this parameter should be a dictionary from type name to type, most easily
            acquired using the built-in ``globals()`` function.
        """
        if is_obj_supported_primitive(obj):
            return obj

        if globals:
            self._custom_serializers = resolve_types(self._custom_serializers, globals)

        result = self._serialize(
            obj, type_key, fully_qualified_types, preserve_iterable_types, inner=False
        )
        return _convert_to_json_serializable(result)

    def _serialize(
        self, obj, type_key, fully_qualified_types, preserve_iterable_types, inner=True
    ):
        serialization_method = self._custom_serializers.get(type(obj))
        if serialization_method:
            result = serialization_method(obj)
        else:
            try:
                result = self._serialize_data_class(
                    obj, type_key, fully_qualified_types, preserve_iterable_types
                )
            except TypeError:
                if isinstance(obj, Enum):
                    result = {ENUM_VALUE_KEY: obj.value}
                elif isinstance(obj, Mapping):
                    result = self._serialize_mapping(
                        obj, type_key, fully_qualified_types, preserve_iterable_types
                    )
                elif isinstance(obj, Iterable) and not isinstance(obj, str):
                    serialized = self._serialize_iterable(
                        obj, type_key, fully_qualified_types, preserve_iterable_types
                    )
                    if type_key is None or not preserve_iterable_types:
                        return serialized
                    result = {ITERABLE_VALUE_KEY: serialized}
                elif not inner:
                    raise
                else:
                    return obj

        if type_key is not None:
            self._add_type_data(result, obj, type_key, fully_qualified_types)
        return result

    def _serialize_data_class(
        self, obj, type_key, fully_qualified_types, preserve_iterable_types
    ):
        fields = get_fields(type(obj))
        result = {
            f.name: self._serialize(
                getattr(obj, f.name),
                type_key,
                fully_qualified_types,
                preserve_iterable_types,
            )
            for f in fields
        }
        self._warn_for_possible_problems_in_deserialization(obj, fields, result)
        return result

    def _serialize_iterable(
        self, obj: Iterable, type_key, fully_qualified_types, preserve_iterable_types
    ):
        return [
            self._serialize(
                item, type_key, fully_qualified_types, preserve_iterable_types
            )
            for item in obj
        ]

    def _serialize_mapping(
        self, obj: Mapping, type_key, fully_qualified_types, preserve_iterable_types
    ):
        if any(not is_obj_supported_primitive(k) for k in obj.keys()):
            raise ValueError(
                f"Mapping {obj} contains a key which is not json-serializable"
            )
        return {
            k: self._serialize(
                v, type_key, fully_qualified_types, preserve_iterable_types
            )
            for k, v in obj.items()
        }

    @staticmethod
    def _warn_for_possible_problems_in_deserialization(
        obj, fields: Iterable[Field], data: Dict[str, Any],
    ) -> None:
        for f in fields:
            try:
                value = data[f.name]
                if f.converter is not None:
                    value = f.converter(value)
            except:
                _logger.warning(
                    f'Field "{f.name}" in obj "{obj.__class__.__name__}" has value {data[f.name]} that could not be converted using its converter'
                )
                continue

            if f.validator is not None and not isinstance(data[f.name], dict):
                try:
                    f.validator(obj, f, value)
                except:
                    _logger.warning(
                        f'Field "{f.name}" in obj "{obj.__class__.__name__}" has value {value} that doesn\'t match this field\'s validator'
                    )
                    continue
            if f.converter is not None:
                _logger.warning(
                    f'Field "{f.name}" in obj "{obj.__class__.__name__}" has a converter'
                )

    @staticmethod
    def _add_type_data(data, obj, type_key, fully_qualified_types):
        class_name = obj.__class__.__name__
        if fully_qualified_types:
            type_value = ".".join((obj.__class__.__module__, class_name))
        else:
            type_value = class_name
        data[type_key] = type_value


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
