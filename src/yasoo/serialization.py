import logging
from enum import Enum
from inspect import signature
from typing import Dict, Any, Union, Mapping, Iterable, Callable, Type, Optional

from .constants import ENUM_VALUE_KEY
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
        :param globals: If custom serialization methods were registered and used forward reference
            ('Foo' instead of Foo), this parameter should be a dictionary from type name to type, most easily
            acquired using the built-in ``globals()`` function.
        """
        if is_obj_supported_primitive(obj):
            return obj

        if globals:
            self._custom_serializers = resolve_types(self._custom_serializers, globals)

        result = self._serialize(obj, type_key, fully_qualified_types, inner=False)
        return _convert_to_json_serializable(result)

    def _serialize(self, obj, type_key, fully_qualified_types, inner=True):
        if isinstance(obj, list):
            return [
                self._serialize(item, type_key, fully_qualified_types, inner=inner)
                for item in obj
            ]

        serialization_method = self._custom_serializers.get(type(obj))
        if serialization_method:
            result = serialization_method(obj)
        else:
            try:
                fields = get_fields(type(obj))
                result = {
                    f.name: self._serialize(
                        getattr(obj, f.name), type_key, fully_qualified_types,
                    )
                    for f in fields
                }
                self._warn_for_possible_problems_in_deserialization(obj, fields, result)
            except TypeError:
                if isinstance(obj, Enum):
                    result = {ENUM_VALUE_KEY: obj.value}
                elif not inner:
                    raise
                else:
                    return obj

        if type_key is not None:
            class_name = obj.__class__.__name__
            if fully_qualified_types:
                type_value = ".".join((obj.__class__.__module__, class_name))
            else:
                type_value = class_name
            result[type_key] = type_value
        return result

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
