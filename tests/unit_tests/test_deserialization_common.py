from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar
from unittest import TestCase

from yasoo import deserialize, deserializer_of, deserializer
from yasoo.constants import ENUM_VALUE_KEY, ITERABLE_VALUE_KEY

from tests.test_classes import FooContainer, MyMapping

_TYPE_KEY = '__type'


class TestSerializationCommon(TestCase):
    def test_deserialization_of_primitives(self):
        self.assertEqual(True, deserialize(True))
        self.assertEqual(5, deserialize(5))
        self.assertEqual(5.5, deserialize(5.5))
        self.assertEqual('5', deserialize('5'))
        self.assertEqual(None, deserialize(None))

    def test_deserialization_unknown_type_raises_error(self):
        self.assertRaises(ValueError, deserialize, {})

    def test_enum_deserialization(self):
        class Foo(Enum):
            A = 5
            B = 89

        obj = deserialize({ENUM_VALUE_KEY: 5}, obj_type=Foo, globals=locals())
        self.assertEqual(type(obj), Foo)
        self.assertEqual(obj, Foo.A)

    def test_deserializer_registration(self):
        class Foo:
            pass

        @deserializer_of(Foo)
        def func(_):
            return Foo()

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_static_method(self):
        class Foo:
            pass

        class Bar:
            # noinspection PyNestedDecorators
            @deserializer_of(Foo)
            @staticmethod
            def func(_):
                return Foo()

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_forward_ref(self):
        class Foo:
            pass

            @staticmethod
            @deserializer_of('Foo')
            def func(_):
                return Foo()

        f = deserialize({}, Foo, globals=locals())
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_type_hint(self):
        class Foo:
            pass

        @deserializer
        def func(_) -> Foo:
            return Foo()

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_type_hint_forward_ref(self):
        class Foo:
            pass

            @staticmethod
            @deserializer
            def func(_) -> 'Foo':
                return Foo()

        f = deserialize({}, Foo, globals=locals())
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_user_defined_generic(self):
        T = TypeVar('T')

        class Foo(Generic[T]):
            pass

        @deserializer
        def func(_) -> Foo:
            return Foo()

        f = deserialize({}, Foo[int])
        self.assertIsInstance(f, Foo)

    def test_deserializer_registration_user_defined_generic_different_args(self):
        T = TypeVar('T')

        class Foo(Generic[T]):
            def __init__(self, a) -> None:
                super().__init__()
                self.a = a

        @deserializer
        def func(_) -> Foo[int]:
            return Foo('func')

        @deserializer
        def func2(_) -> Foo[str]:
            return Foo('func2')

        f = deserialize({}, Foo[int])
        self.assertIsInstance(f, Foo)
        self.assertEqual('func', f.a)

        f = deserialize({}, Foo[str])
        self.assertIsInstance(f, Foo)
        self.assertEqual('func2', f.a)

    def test_deserializer_registration_datetime_overrides_default(self):
        _datetime = datetime.now()

        @deserializer_of(datetime)
        def foo(d: dict) -> datetime:
            return _datetime

        self.assertEqual(_datetime, deserialize({'time': 0}, datetime, type_key=None))

    def test_serializer_registration_including_descendants(self):
        class Foo:
            pass

        class Bar(Foo):
            pass

        @deserializer_of(Foo, include_descendants=True)
        def foo(_, obj_type=Foo) -> Foo:
            return obj_type()

        self.assertIsInstance(deserialize({}, Foo, type_key=None), Foo)
        self.assertNotIsInstance(deserialize({}, Foo, type_key=None), Bar)
        self.assertIsInstance(deserialize({}, Bar, type_key=None), Bar)

    def test_deserialization_of_list(self):
        class Foo:
            pass

        @deserializer
        def deserialize_foo(_) -> Foo:
            return Foo()

        list_len = 5
        deserialized = deserialize([{_TYPE_KEY: 'Foo'} for _ in range(list_len)], type_key=_TYPE_KEY, globals=locals())
        self.assertIsInstance(deserialized, list)
        self.assertEqual(list_len, len(deserialized))
        for f in deserialized:
            self.assertIsInstance(f, Foo)

    def test_deserialization_of_inner_list_of_primitives_with_type_data(self):
        self._check_deserialization_of_inner_iterable_of_primitives(list, True)

    def test_deserialization_of_inner_set_of_primitives_with_type_data(self):
        self._check_deserialization_of_inner_iterable_of_primitives(set, True)

    def test_deserialization_of_inner_tuple_of_primitives_with_type_data(self):
        self._check_deserialization_of_inner_iterable_of_primitives(tuple, True)

    def test_deserialization_of_inner_list_of_primitives_without_type_data(self):
        self._check_deserialization_of_inner_iterable_of_primitives(list, False)

    def test_deserialization_of_inner_set_of_primitives_without_type_data(self):
        self._check_deserialization_of_inner_iterable_of_primitives(set, False)

    def test_deserialization_of_inner_tuple_of_primitives_without_type_data(self):
        self._check_deserialization_of_inner_iterable_of_primitives(tuple, False)

    def test_deserialization_of_inner_list_of_classes(self):
        self._check_deserialization_of_inner_iterable_of_classes(list)

    def test_deserialization_of_inner_set_of_classes(self):
        self._check_deserialization_of_inner_iterable_of_classes(set)

    def test_deserialization_of_inner_tuple_of_classes(self):
        self._check_deserialization_of_inner_iterable_of_classes(set)

    def test_deserialization_of_inner_dict_of_primitives(self):
        self._check_deserialization_of_inner_mapping_of_primitives(dict)

    def test_deserialization_of_inner_custom_mapping_of_primitives(self):
        self._check_deserialization_of_inner_mapping_of_primitives(MyMapping)

    def test_deserialization_of_inner_dict_of_classes(self):
        self._check_deserialization_of_inner_mapping_of_classes(dict)

    def test_deserialization_of_inner_custom_mapping_of_classes(self):
        self._check_deserialization_of_inner_mapping_of_classes(MyMapping)

    def _check_deserialization_of_inner_iterable_of_primitives(self, iterable_type, include_type_data):
        it = iterable_type(range(5))
        foo = list(it)
        if include_type_data:
            foo = {_TYPE_KEY: iterable_type.__name__, ITERABLE_VALUE_KEY: foo}
        deserialized = deserialize({
            _TYPE_KEY: FooContainer.__name__,
            'foo': foo
        },
            type_key=_TYPE_KEY,
            globals=globals())
        self.assertIsInstance(deserialized, FooContainer)
        if include_type_data:
            self.assertIsInstance(deserialized.foo, iterable_type)
            self.assertEqual(it, deserialized.foo)
        else:
            self.assertIsInstance(deserialized.foo, list)
            self.assertEqual(list(it), deserialized.foo)

    def _check_deserialization_of_inner_iterable_of_classes(self, iterable_type):
        class Foo:
            pass

        @deserializer
        def deserialize_foo(_) -> Foo:
            return Foo()

        it = [{_TYPE_KEY: 'Foo'} for _ in range(5)]
        deserialized = deserialize({
            _TYPE_KEY: FooContainer.__name__,
            'foo': {_TYPE_KEY: iterable_type.__name__, ITERABLE_VALUE_KEY: it}
        },
            type_key=_TYPE_KEY,
            globals=dict(locals(), **globals()))
        self.assertIsInstance(deserialized, FooContainer)
        self.assertIsInstance(deserialized.foo, iterable_type)
        self.assertEqual(len(it), len(deserialized.foo))
        for f in deserialized.foo:
            self.assertIsInstance(f, Foo)

    def _check_deserialization_of_inner_mapping_of_primitives(self, mapping_type):
        m = mapping_type({i: i**2 for i in range(5)})
        deserialized = deserialize({
            _TYPE_KEY: FooContainer.__name__,
            'foo': dict(m, **{_TYPE_KEY: mapping_type.__name__})
        },
            type_key=_TYPE_KEY,
            globals=globals())
        self.assertIsInstance(deserialized, FooContainer)
        self.assertIsInstance(deserialized.foo, mapping_type)
        self.assertEqual(m, deserialized.foo)

    def _check_deserialization_of_inner_mapping_of_classes(self, mapping_type):
        class Foo:
            pass

        @deserializer
        def deserialize_foo(_) -> Foo:
            return Foo()

        m = {i: {_TYPE_KEY: 'Foo'} for i in range(5)}
        deserialized = deserialize({
            _TYPE_KEY: FooContainer.__name__,
            'foo': dict(m, **{_TYPE_KEY: mapping_type.__name__})
        },
            type_key=_TYPE_KEY,
            globals=dict(locals(), **globals()))
        self.assertIsInstance(deserialized, FooContainer)
        self.assertIsInstance(deserialized.foo, mapping_type)
        self.assertEqual(len(m), len(deserialized.foo))
        for k in m.keys():
            self.assertIsInstance(deserialized.foo[k], Foo)
