from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from unittest import TestCase

from attr import attrs, attrib

from tests.test_classes import AttrsClass
from yasoo import deserialize, deserializer_of, deserializer
from yasoo.constants import ENUM_VALUE_KEY


class DeserializationTests(TestCase):
    def test_attr_deserialization(self):
        @attrs
        class Foo:
            a = attrib()

        f = deserialize({'a': 5}, Foo)
        self.assertEqual(type(f), Foo)
        self.assertEqual(f.a, 5)

    def test_attr_missing_fields(self):
        @attrs
        class Foo:
            a = attrib()
            bar = attrib(default=None)

        try:
            deserialize({'a': 5}, Foo)
        except:
            self.fail('Failed to deserialize with non-mandatory field missing')

        try:
            deserialize({'bar': 5}, Foo)
            self.fail('Deserialized even though mandatory field is missing')
        except:
            pass

    def test_attr_extraneous_fields(self):
        @attrs
        class Foo:
            pass

        try:
            deserialize({'a': 5}, Foo)
            self.fail('Deserialized with extraneous fields')
        except:
            pass

    def test_attr_deserialization_with_type_in_data(self):
        @attrs
        class Foo:
            a = attrib()

        @attrs
        class Bar:
            foo = attrib()

        b = deserialize({'__type': 'Bar', 'foo': {'a': 5, '__type': 'Foo'}}, type_key='__type', globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), Foo)
        self.assertEqual(b.foo.a, 5)

    def test_attr_deserialization_with_fully_qualified_type_in_data(self):
        @attrs
        class Bar:
            foo = attrib()

        fully_qualified_name = '.'.join([AttrsClass.__module__, AttrsClass.__name__])
        b = deserialize({'__type': 'Bar', 'foo': {'__type': fully_qualified_name}},
                        obj_type=Bar,
                        type_key='__type',
                        globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), AttrsClass)

    def test_attr_deserialization_with_type_hint(self):
        @attrs
        class Foo:
            a = attrib()

        @attrs
        class Bar:
            foo: Foo = attrib()

        b = deserialize({'foo': {'a': 5}}, Bar, globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), Foo)
        self.assertEqual(b.foo.a, 5)

    def test_attr_deserialization_with_type_hint_and_type_in_data(self):
        @attrs
        class Foo:
            a = attrib()

        @attrs
        class FakeFoo:
            a = attrib()

        @attrs
        class Bar:
            foo: FakeFoo = attrib()

        b = deserialize({'__type': 'Bar', 'foo': {'a': 5, '__type': 'Foo'}}, type_key='__type', globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), Foo)
        self.assertEqual(b.foo.a, 5)

    def test_dataclass_deserialization(self):
        @dataclass
        class Foo:
            a: Any

        f = deserialize({'a': 5}, Foo)
        self.assertEqual(type(f), Foo)
        self.assertEqual(f.a, 5)

    def test_dataclass_missing_fields(self):
        @dataclass
        class Foo:
            a: Any
            bar: Any = field(default=None)

        try:
            deserialize({'a': 5}, Foo, None)
        except:
            self.fail('Failed to deserialize with non-mandatory field missing')

        try:
            deserialize({'bar': 5}, Foo, None)
            self.fail('Deserialized even though mandatory field is missing')
        except:
            pass

    def test_dataclass_extraneous_fields(self):
        @dataclass
        class Foo:
            pass

        try:
            deserialize({'a': 5}, Foo)
            self.fail('Deserialized with extraneous fields')
        except:
            pass

    def test_dataclass_deserialization_with_type_in_data(self):
        @dataclass
        class Foo:
            a: Any

        @dataclass
        class Bar:
            foo: Any

        b = deserialize({'__type': 'Bar', 'foo': {'a': 5, '__type': 'Foo'}}, type_key='__type', globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), Foo)
        self.assertEqual(b.foo.a, 5)

    def test_dataclass_deserialization_with_fully_qualified_type_in_data(self):
        from tests.test_classes import AttrsClass
        @dataclass
        class Bar:
            foo: Any

        fully_qualified_name = '.'.join([AttrsClass.__module__, AttrsClass.__name__])
        b = deserialize({'__type': 'Bar', 'foo': {'__type': fully_qualified_name}},
                        obj_type=Bar,
                        type_key='__type',
                        globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), AttrsClass)

    def test_dataclass_deserialization_with_type_hint(self):
        @dataclass
        class Foo:
            a: Any

        @dataclass
        class Bar:
            foo: Foo

        b = deserialize({'foo': {'a': 5}}, Bar, globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), Foo)
        self.assertEqual(b.foo.a, 5)

    def test_dataclass_deserialization_with_type_hint_and_type_in_data(self):
        @dataclass
        class Foo:
            a: Any

        @dataclass
        class FakeFoo:
            a: Any

        @dataclass
        class Bar:
            foo: FakeFoo

        b = deserialize({'__type': 'Bar', 'foo': {'a': 5, '__type': 'Foo'}}, type_key='__type', globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), Foo)
        self.assertEqual(b.foo.a, 5)

    def test_enum_deserialization(self):
        class Foo(Enum):
            A = 5
            B = 89

        @attrs
        class Bar:
            foo: Foo = attrib()

        b = deserialize({'foo': {ENUM_VALUE_KEY: 5}}, obj_type=Bar, globals=locals())
        self.assertEqual(type(b), Bar)
        self.assertEqual(type(b.foo), Foo)
        self.assertEqual(b.foo, Foo.A)

    def test_deserializer_registration(self):
        class Foo:
            pass

        @deserializer_of(Foo)
        def func(foo):
            return Foo()

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_static_method(self):
        @attrs
        class Foo:
            a = attrib()

        class Bar:
            @deserializer_of(Foo)
            @staticmethod
            def func(data):
                return Foo(5)

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))
        self.assertEqual(5, f.a)

    def test_deserializer_registration_forward_ref(self):
        @attrs
        class Foo:
            a = attrib()

            @staticmethod
            @deserializer_of('Foo')
            def func(data):
                return Foo(5)

        f = deserialize({}, Foo, globals=locals())
        self.assertEqual(Foo, type(f))
        self.assertEqual(5, f.a)

    def test_deserializer_registration_type_hint(self):
        @attrs
        class Foo:
            a = attrib()

        @deserializer
        def func(data) -> Foo:
            return Foo(5)

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))
        self.assertEqual(5, f.a)

    def test_deserializer_registration_type_hint_forward_ref(self):
        @attrs
        class Foo:
            a = attrib()

            @staticmethod
            @deserializer
            def func(data) -> 'Foo':
                return Foo(5)

        f = deserialize({}, Foo, globals=locals())
        self.assertEqual(Foo, type(f))
        self.assertEqual(5, f.a)
