from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar, Optional, Tuple
from unittest import TestCase

from tests.test_classes import FooContainer, MyMapping, Child
from yasoo import deserialize, deserializer_of, deserializer, unregister_deserializers
from yasoo.constants import ENUM_VALUE_KEY, ITERABLE_VALUE_KEY

_TYPE_KEY = '__type'
T = TypeVar('T')


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

        obj = deserialize({ENUM_VALUE_KEY: Foo.A.name}, obj_type=Foo, globals=locals())
        self.assertEqual(type(obj), Foo)
        self.assertEqual(obj, Foo.A)

    def test_enum_deserialization_case_insensitive(self):
        class Foo(Enum):
            AbC = 5
            B = 89

        obj = deserialize({ENUM_VALUE_KEY: Foo.AbC.name.lower()}, obj_type=Foo, globals=locals())
        self.assertEqual(type(obj), Foo)
        self.assertEqual(obj, Foo.AbC)

    def test_enum_deserialization_by_value(self):
        class Foo(Enum):
            A = 5
            B = 89

        obj = deserialize({ENUM_VALUE_KEY: Foo.A.value}, obj_type=Foo, globals=locals())
        self.assertEqual(type(obj), Foo)
        self.assertEqual(obj, Foo.A)

    def test_enum_deserialization_fallback_order(self):
        class Foo(Enum):
            A = 5
            B = 'a'
            C = 'A'
            D = 'x'

        # Default - by name
        obj = deserialize({ENUM_VALUE_KEY: 'A'}, obj_type=Foo, globals=locals())
        self.assertEqual(obj, Foo.A)
        # Fallback 1 - by case-insensitive name
        obj = deserialize({ENUM_VALUE_KEY: 'a'}, obj_type=Foo, globals=locals())
        self.assertEqual(obj, Foo.A)
        # Fallback 2 - by value
        obj = deserialize({ENUM_VALUE_KEY: 'x'}, obj_type=Foo, globals=locals())
        self.assertEqual(obj, Foo.D)
        # Failure
        with self.assertRaises(ValueError):
            deserialize({ENUM_VALUE_KEY: 'y'}, obj_type=Foo, globals=locals())

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

        # noinspection PyUnusedLocal
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
        class Foo(Generic[T]):
            pass

        @deserializer
        def func(_) -> Foo:
            return Foo()

        f = deserialize({}, Foo[int])
        self.assertIsInstance(f, Foo)

    def test_deserializer_registration_user_defined_generic_different_args(self):
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
        def foo(_) -> datetime:
            return _datetime

        self.assertEqual(_datetime, deserialize({'time': 0}, datetime, type_key=None))

    def test_deserializer_registration_including_descendants(self):
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

    def test_deserializer_temporary_unregister(self):
        class Foo:
            pass

        @deserializer_of(Foo)
        def func(_):
            return Foo()

        with self.assertRaises(TypeError) as e:
            with unregister_deserializers(Foo):
                deserialize({}, Foo, type_key=None)
        self.assertIn('attrs or dataclass classes', e.exception.args[0])
        self.assertIsInstance(deserialize({}, Foo, type_key=None), Foo)

    def test_deserializer_ignore_custom_deserializer(self):
        class Foo:
            pass

        @deserializer_of(Foo)
        def func(_):
            return Foo()

        with self.assertRaises(TypeError) as e:
            with unregister_deserializers(Foo):
                deserialize({}, Foo, type_key=None, ignore_custom_deserializer=True)
        self.assertIn('attrs or dataclass classes', e.exception.args[0])
        self.assertIsInstance(deserialize({}, Foo, type_key=None), Foo)

    def test_deserialization_discovers_globals(self):
        data = {'child': {}}
        result = deserialize(dict(data), Child, globals=globals())
        self.assertIsInstance(result, Child)
        self.assertEqual('Parent', type(result.child).__name__)

        with self.assertRaises(TypeError) as e:
            deserialize(dict(data), Child)
        self.assertIn('Found type annotation Parent', e.exception.args[0])

    def test_deserializer_registration_can_defer_dereference(self):
        class Foo:
            pass

            @staticmethod
            @deserializer
            def func(_) -> 'Foo':
                return Foo()

        with self.assertRaises(Exception):
            f = deserialize({}, Foo, globals=globals())
        f = deserialize({}, Foo, globals=locals())
        self.assertEqual(Foo, type(f))

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

    def test_deserialization_of_list_with_generic_type_hint(self):
        class Foo:
            pass

        @deserializer
        def deserialize_foo(_) -> Foo:
            return Foo()

        deserialized = deserialize([{'__type': 'Foo'}, {'__type': 'Foo'}], obj_type=T, globals=locals())
        self.assertIsInstance(deserialized, list)
        self.assertEqual(2, len(deserialized))
        self.assertTrue(all(isinstance(f, Foo) for f in deserialized))

    def test_deserialization_of_iterable_with_type_hint_longer_than_data(self):
        deserialized = deserialize([], Tuple[int, bool, int])
        self.assertIsInstance(deserialized, list)
        self.assertEqual(0, len(deserialized))

    def test_deserialization_of_iterable_with_type_hint_optional(self):
        class Foo:
            pass

        @deserializer_of(Foo)
        def deserializer_foo(_) -> Foo:
            return Foo()

        deserialized = deserialize([1, {}, 2], Optional[Tuple[int, Foo, int]])
        self.assertIsInstance(deserialized, list)
        self.assertEqual(3, len(deserialized))
        self.assertIsInstance(deserialized[1], Foo)

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

    def test_deserialization_with_string_type_hint(self):
        class Foo:
            pass

        @deserializer_of(Foo)
        def deserialize_foo(_):
            return Foo()

        foo = deserialize({}, 'Foo', type_key=None, globals=locals())
        self.assertIsInstance(foo, Foo)

        with self.assertRaises(TypeError) as e:
            deserialize({}, 'Bar', type_key=None, globals=locals())
        self.assertIn('Bar', e.exception.args[0])

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
