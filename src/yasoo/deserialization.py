import datetime
import json
from contextlib import contextmanager
from enum import Enum
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
from .default_customs import (
    deserialize_type,
    deserialize_time,
    deserialize_datetime,
    deserialize_date,
)
from .objects import DictWithSerializedKeys
from .utils import (
    resolve_types,
    get_fields,
    normalize_method,
    normalize_type,
    is_obj_supported_primitive,
    SUPPORTED_PRIMITIVES,
    fully_qualified_string_to_type,
    NoneType,
)

T = TypeVar("T")


class Deserializer:
    def __init__(self) -> None:
        super().__init__()
        t = Dict[type, Callable[[Dict[str, Any], Type[T]], T]]
        self._custom_deserializers: Dict[Type[T], Callable[[Dict[str, Any]], T]] = {
            datetime.date: deserialize_date,
            datetime.time: deserialize_time,
            datetime.datetime: deserialize_datetime,
        }
        self._inheritance_deserializers: t = {
            type: deserialize_type,
        }

    def register(
        self,
        type_to_register: Optional[Union[Type[T], str]] = None,
        include_descendants: bool = False,
    ):
        """
        Registers a custom deserialization method that takes a dictionary and returns an instance of the registered
        type.

        :param type_to_register: The type of objects this method deserializes to. Can be a string, but then
            ``deserialize`` should be called with the ``globals`` parameter.
        :param include_descendants: Whether to use the registered method for objects inheriting from the given type
            or only for objects of the given type itself.
        """

        def registration_method(
            deserialization_method: Union[Callable[[Dict[str, Any]], T], staticmethod]
        ):
            method = normalize_method(deserialization_method)
            t = type_to_register
            if t is None:
                t = signature(method).return_annotation
            self._custom_deserializers[t] = method
            if include_descendants:
                self._inheritance_deserializers[t] = method
            return deserialization_method

        return registration_method

    @contextmanager
    def unregister(self, *types: Type[T]):
        """
        Temporarily unregisters registered deserializers, so ``deserialize`` will use the default deserialization
        algorithm.

        :param types: The types to deserialize using the default algorithm.
        :return:
        """
        types_funcs = [
            (type_, self._custom_deserializers.pop(type_, None)) for type_ in types
        ]
        try:
            yield
        finally:
            for type_, func in types_funcs:
                if func is not None:
                    self._custom_deserializers[type_] = func

    @overload
    def deserialize(
        self,
        data: Optional[Union[bool, int, float, str, list, Dict[str, Any]]],
        obj_type: Callable[[], T],
        type_key: Optional[str] = "__type",
        allow_extra_fields: bool = False,
        ignore_custom_deserializer: bool = False,
        globals: Optional[Dict[str, Any]] = None,
    ) -> T:
        ...

    def deserialize(
        self,
        data: Optional[Union[bool, int, float, str, list, Dict[str, Any]]],
        obj_type: Optional[Type[T]] = None,
        type_key: Optional[str] = "__type",
        allow_extra_fields: bool = False,
        ignore_custom_deserializer: bool = False,
        globals: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Deserializes an object from a dictionary or a list of dictionaries,
        or returns the object itself if it's a primitive (including ``None``).

        :param data: The dictionary.
        :param obj_type: The type of the object to deserialize. Can only be ``None`` if ``data`` contains a type key.
        :param type_key: The key in ``data`` that contains the type name for non-primitive objects.
            Can be ``None`` if this key was omitted during serialization and deserialization should rely on type hints.
        :param allow_extra_fields: Whether to throw an exception if the data contains fields that are not in the type
            definition, or just ignore them.
        :param ignore_custom_deserializer: Whether to ignore the custom deserializer for this obj_type and use the
            default serializer instead. This only applies to the top level object, not to any inner objects
            (see ``unregister`` for ignoring custom deserializer for inner objects as well).
        :param globals: A dictionary from type name to type, most easily acquired using the built-in ``globals()``
            function.
        """
        if globals:
            self._custom_deserializers = resolve_types(
                self._custom_deserializers, globals
            )

        return self._deserialize(
            data,
            obj_type,
            type_key,
            allow_extra_fields,
            globals or {},
            ignore_custom_deserializer,
        )

    def _deserialize(
        self,
        data: Optional[Union[bool, int, float, str, list, Dict[str, Any]]],
        obj_type: Optional[Type[T]],
        type_key: Optional[str],
        allow_extra_fields: bool,
        external_globals: Dict[str, Any],
        ignore_custom_deserializer: bool = False,
    ):
        all_globals = dict(globals())
        all_globals.update(external_globals)
        if is_obj_supported_primitive(data):
            return data
        if isinstance(data, list):
            list_types = self._get_list_types(obj_type, data)
            return [
                self._deserialize(d, t, type_key, allow_extra_fields, all_globals)
                for t, d in list_types
            ]

        obj_type = self._get_object_type(obj_type, data, type_key, all_globals)
        if type_key in data:
            data.pop(type_key)
        real_type, generic_args = normalize_type(obj_type, all_globals)
        if external_globals and isinstance(real_type, type):
            bases = {real_type}
            while bases:
                all_globals.update((b.__name__, b) for b in bases)
                bases = {ancestor for b in bases for ancestor in b.__bases__}

        if not ignore_custom_deserializer:
            deserialization_method = self._custom_deserializers.get(
                obj_type, self._custom_deserializers.get(real_type)
            )
            if deserialization_method:
                return deserialization_method(data)
            for base_class, method in self._inheritance_deserializers.items():
                if issubclass(real_type, base_class):
                    return method(data, real_type)

        key_type = None
        try:
            fields = {f.name: f for f in get_fields(obj_type)}
        except TypeError:
            if issubclass(real_type, Enum):
                value = data[ENUM_VALUE_KEY]
                if isinstance(value, str):
                    try:
                        return real_type[value]
                    except KeyError:
                        for e in real_type:
                            if e.name.lower() == value.lower():
                                return e
                return real_type(value)
            elif issubclass(real_type, Mapping):
                key_type = generic_args[0] if generic_args else None
                if self._is_mapping_dict_with_serialized_keys(key_type, data):
                    obj_type = DictWithSerializedKeys
                    fields = {f.name: f for f in get_fields(obj_type)}
                    value_type = generic_args[1] if generic_args else Any
                    fields["data"].field_type = Dict[str, value_type]
                else:
                    return self._load_mapping(
                        data,
                        real_type,
                        generic_args,
                        type_key,
                        allow_extra_fields,
                        all_globals,
                    )
            elif issubclass(real_type, Iterable):
                # If we got here it means data is not a list, so obj_type came from the data itself and is safe to use
                return self._load_iterable(
                    data, obj_type, type_key, allow_extra_fields, all_globals
                )
            elif real_type != obj_type:
                return self._deserialize(
                    data, real_type, type_key, allow_extra_fields, external_globals
                )
            else:
                raise

        self._check_for_missing_fields(data, fields, obj_type)
        self._check_for_extraneous_fields(data, fields, obj_type, allow_extra_fields)
        self._load_inner_fields(data, fields, type_key, allow_extra_fields, all_globals)
        if obj_type is DictWithSerializedKeys:
            return self._load_dict_with_serialized_keys(
                obj_type(**data), key_type, type_key, allow_extra_fields, all_globals
            )
        kwargs = {k: v for k, v in data.items() if fields[k].init}
        result = obj_type(**kwargs)
        for k, v in data.items():
            if k not in kwargs:
                setattr(result, k, v)
        return result

    def _load_dict_with_serialized_keys(
        self,
        obj: DictWithSerializedKeys,
        key_type,
        type_key,
        allow_extra_fields,
        all_globals,
    ):
        data = {
            self._deserialize(
                json.loads(k), key_type, type_key, allow_extra_fields, all_globals
            ): v
            for k, v in obj.data.items()
        }
        obj_type = Deserializer._get_type(obj.original_type, all_globals)
        return obj_type(data)

    def _load_mapping(
        self,
        data: Mapping,
        obj_type,
        generic_args,
        type_key,
        allow_extra_fields,
        all_globals,
    ):
        val_type = generic_args[1] if len(generic_args) > 1 else None
        return obj_type(
            {
                k: self._deserialize(
                    v, val_type, type_key, allow_extra_fields, all_globals
                )
                for k, v in data.items()
            }
        )

    def _load_iterable(self, data, obj_type, type_key, allow_extra_fields, all_globals):
        return obj_type(
            self._deserialize(i, None, type_key, allow_extra_fields, all_globals)
            for i in data[ITERABLE_VALUE_KEY]
        )

    def _load_inner_fields(
        self, data, fields, type_key, allow_extra_fields, all_globals
    ):
        for key, value in data.items():
            field = fields[key]
            data[key] = self._deserialize(
                value, field.field_type, type_key, allow_extra_fields, all_globals
            )

    @classmethod
    def _is_mapping_dict_with_serialized_keys(cls, key_type, data):
        if (
            key_type
            and key_type not in SUPPORTED_PRIMITIVES
            and key_type is not NoneType
        ):
            return True
        if key_type is str:
            return False

        fields = {f.name: f for f in get_fields(DictWithSerializedKeys)}
        try:
            cls._check_for_missing_fields(data, fields, DictWithSerializedKeys)
        except ValueError:
            return False
        return True

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
    def _check_for_extraneous_fields(data, fields, obj_type, allow_extra_fields):
        extraneous = set(data.keys()).difference(fields)
        if extraneous and not allow_extra_fields:
            extraneous_str = '", "'.join(extraneous)
            raise ValueError(
                f'Found extraneous fields "{extraneous_str}" for object type "{obj_type.__name__}".'
                f"Data is:\n{json.dumps(data)}"
            )
        for e in extraneous:
            data.pop(e)

    @staticmethod
    def _get_list_types(
        type_hint: Optional[type], data: list
    ) -> List[Tuple[Optional[type], Any]]:
        generic_args = None
        try:
            if type_hint is not None:
                _, generic_args = normalize_type(type_hint)
        except TypeError:
            pass
        if generic_args is None:
            return [(None, item) for item in data]
        if len(generic_args) == 1 or (
            len(generic_args) == 2 and generic_args[1] is ...
        ):
            return [(generic_args[0], item) for item in data]
        if len(generic_args) >= len(data):
            return list(zip(generic_args, data))
        return list(zip_longest(generic_args, data))

    @staticmethod
    def _get_object_type(
        obj_type: Optional[Type[T]],
        data: Dict[str, Any],
        type_key: str,
        all_globals: Dict[str, Any],
    ) -> type:
        if type_key in data:
            return Deserializer._get_type(data[type_key], all_globals)
        if obj_type is None or obj_type is Any:
            raise ValueError(
                f"type key not found in data and obj type could not be inferred.\nData: {json.dumps(data)}"
            )
        return obj_type

    @staticmethod
    def _get_type(type_name: str, all_globals: Dict[str, Any]) -> type:
        if "." not in type_name:
            return Deserializer._get_non_fully_qualified_type(type_name, all_globals)
        return fully_qualified_string_to_type(type_name)

    @staticmethod
    def _get_non_fully_qualified_type(
        type_name: str, all_globals: Dict[str, Any]
    ) -> type:
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
