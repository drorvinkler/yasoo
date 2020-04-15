from enum import Enum
from unittest import TestCase

from yasoo import deserialize, deserializer_of, deserializer
from yasoo.constants import ENUM_VALUE_KEY

from tests.test_classes import FooContainer


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

    def test_deserialization_of_list(self):
        class Foo:
            pass

        @deserializer
        def deserialize_foo(_) -> Foo:
            return Foo()

        type_key = '__type'
        list_len = 5
        deserialized = deserialize([{type_key: 'Foo'} for _ in range(list_len)], type_key=type_key, globals=locals())
        self.assertIsInstance(deserialized, list)
        self.assertEqual(list_len, len(deserialized))
        for f in deserialized:
            self.assertIsInstance(f, Foo)

    def test_deserialization_of_inner_list_of_primitives(self):
        type_key = '__type'
        list_len = 5
        list_val = 1
        deserialized = deserialize({
            type_key: FooContainer.__name__,
            'foo': [list_val] * list_len
        },
            type_key=type_key,
            globals=dict(locals(), **globals()))
        self.assertIsInstance(deserialized, FooContainer)
        self.assertIsInstance(deserialized.foo, list)
        self.assertEqual(list_len, len(deserialized.foo))
        for f in deserialized.foo:
            self.assertEqual(f, list_val)

    def test_deserialization_of_inner_list_of_classes(self):
        class Foo:
            pass

        @deserializer
        def deserialize_foo(_) -> Foo:
            return Foo()

        type_key = '__type'
        list_len = 5
        deserialized = deserialize({
            type_key: FooContainer.__name__,
            'foo': [{type_key: 'Foo'} for _ in range(list_len)]
        },
            type_key=type_key,
            globals=dict(locals(), **globals()))
        self.assertIsInstance(deserialized, FooContainer)
        self.assertIsInstance(deserialized.foo, list)
        self.assertEqual(list_len, len(deserialized.foo))
        for f in deserialized.foo:
            self.assertIsInstance(f, Foo)
