from enum import Enum
from inspect import signature
from typing import Dict, Any, Union, Mapping, Iterable, Callable, Type, Optional

from yasoo.constants import ENUM_VALUE_KEY
from yasoo.utils import resolve_types, get_fields, normalize_method


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
        def registration_method(serialization_method: Union[Callable[[Any], Dict[str, Any]], staticmethod]):
            method = normalize_method(serialization_method)
            t = type_to_register
            if t is None:
                t = next(iter(signature(method).parameters.values())).annotation
            self._custom_serializers[t] = method
            return serialization_method

        return registration_method

    def serialize(self,
                  obj,
                  type_key: Optional[str] = '__type',
                  fully_qualified_types: bool = True,
                  globals: Optional[Dict[str, Any]] = None
                  ) -> Dict[str, Any]:
        """
        Serializes an object to a json-serializable dictionary.

        :param obj: The object to serialize.
        :param type_key: The key in the resulting dictionary to contain the type name for non-primitive objects.
            Can be ``None`` to omit this key and rely on type hints when deserializing.
        :param fully_qualified_types: Whether to use fully qualified type names in the ``type_key``,
            i.e. whether to write "my_package.MyType" or just "MyType".
        :param globals: If custom serialization methods were registered and used forward reference
            ('Foo' instead of Foo), this parameter should be a dictionary from type name to type, most easily
            acquired using the built-in ``globals()`` function.
        """
        if globals:
            self._custom_serializers = resolve_types(self._custom_serializers, globals)
        result = self._serialize(obj, type_key, fully_qualified_types, inner=False)
        return _convert_to_json_serializable(result)

    def _serialize(self, obj, type_key, fully_qualified_types, inner=True):
        serialization_method = self._custom_serializers.get(type(obj))
        if serialization_method:
            result = serialization_method(obj)
        else:
            try:
                field_names = [f.name for f in get_fields(type(obj))]
                result = {f: self._serialize(getattr(obj, f), type_key, fully_qualified_types)
                          for f in field_names}
            except TypeError:
                if isinstance(obj, Enum):
                    result = {ENUM_VALUE_KEY: obj.value}
                elif not inner:
                    raise
                else:
                    return obj

        if type_key is not None:
            type_value = '.'.join(
                (obj.__class__.__module__, obj.__class__.__name__)) if fully_qualified_types else obj.__class__.__name__
            result[type_key] = type_value
        return result


def _convert_to_json_serializable(obj) -> Union[int, float, str, list, dict, None]:
    if isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, str) or obj is None:
        return obj
    if isinstance(obj, Mapping):
        return {key: _convert_to_json_serializable(value) for key, value in obj.items()}
    if isinstance(obj, Iterable):
        return [_convert_to_json_serializable(item) for item in obj]
    raise TypeError('Found object of type "{}" which cannot be serialized'.format(type(obj).__name__))
