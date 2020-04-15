from enum import Enum
from unittest import TestCase

from yasoo import serialize, serializer, serializer_of
from yasoo.constants import ENUM_VALUE_KEY

from tests.test_classes import FooContainer


class TestSerializationCommon(TestCase):
    def test_serialization_of_primitives(self):
        self.assertEqual(True, serialize(True))
        self.assertEqual(5, serialize(5))
        self.assertEqual(5.5, serialize(5.5))
        self.assertEqual('5', serialize('5'))
        self.assertEqual(None, serialize(None))

    def test_enum_serialization(self):
        class Foo(Enum):
            A = 5
            B = 89

        s = serialize(Foo.A)
        self.assertEqual(Foo.A.value, s[ENUM_VALUE_KEY])

    def test_serializer_registration(self):
        class Foo:
            pass

        @serializer_of(Foo)
        def func(_):
            return {'foo': 'bar'}

        s = serialize(Foo())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_static_method(self):
        class Foo:
            pass

        class Bar:
            # noinspection PyNestedDecorators
            @serializer_of(Foo)
            @staticmethod
            def func(_):
                return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_forward_ref(self):
        class Foo:
            @staticmethod
            @serializer_of('Foo')
            def func(_):
                return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_type_hint(self):
        class Foo:
            pass

        @serializer
        def func(_: Foo):
            return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_type_hint_forward_ref(self):
        class Foo:
            @staticmethod
            @serializer
            def func(_: 'Foo'):
                return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serialization_regular_class_raises_error(self):
        class Foo:
            pass

        self.assertRaises(TypeError, serialize, Foo())

    def test_serialization_inner_regular_class_raises_error(self):
        class Foo:
            pass

        class Bar:
            pass

        @serializer
        def serialize_foo(_: Foo):
            return {'bar': Bar()}

        self.assertRaises(TypeError, serialize, Foo())

    def test_serialization_of_list(self):
        class Foo:
            pass

        @serializer
        def deserialize_foo(_: Foo):
            return {}

        type_key = '__type'
        list_len = 5
        s = serialize([Foo() for _ in range(list_len)], type_key=type_key, fully_qualified_types=False, globals=locals())
        self.assertIsInstance(s, list)
        self.assertEqual(list_len, len(s))
        for d in s:
            self.assertEqual({type_key: 'Foo'}, d)

    def test_serialization_of_inner_list_of_primitives(self):
        type_key = '__type'
        list_len = 5
        list_val = 1
        s = serialize(FooContainer(foo=[list_val] * list_len),
                      type_key=type_key,
                      fully_qualified_types=False,
                      globals=locals())
        self.assertIsInstance(s, dict)
        self.assertIn('foo', s)

        foo = s['foo']
        self.assertIsInstance(foo, list)
        self.assertEqual(list_len, len(foo))
        for d in foo:
            self.assertEqual(list_val, d)

    def test_serialization_of_inner_list_of_classes(self):
        class Foo:
            pass

        @serializer
        def deserialize_foo(_: Foo):
            return {}

        type_key = '__type'
        list_len = 5
        s = serialize(FooContainer(foo=[Foo() for _ in range(list_len)]),
                      type_key=type_key,
                      fully_qualified_types=False,
                      globals=locals())
        self.assertIsInstance(s, dict)
        self.assertIn('foo', s)

        foo = s['foo']
        self.assertIsInstance(foo, list)
        self.assertEqual(list_len, len(foo))
        for d in foo:
            self.assertEqual({type_key: 'Foo'}, d)
