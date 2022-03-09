from typing import Any, Dict, Sequence
from unittest import TestCase

from yasoo import deserialize

try:
    from dataclasses import dataclass, field

    DATACLASSES_EXIST = True
except ModuleNotFoundError:
    DATACLASSES_EXIST = False


if DATACLASSES_EXIST:
    class TestDataclassDeserialization(TestCase):
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

        def test_dataclass_deserialization_with_generic_sequence_type_hint(self):
            @dataclass
            class Foo:
                a: Any

            @dataclass
            class Bar:
                foo: Sequence[Foo]

            b = deserialize({'foo': [{'a': 5}]}, Bar, globals=locals())
            self.assertIsInstance(b, Bar)
            self.assertIsInstance(b.foo, list)
            self.assertEqual(1, len(b.foo))
            self.assertIsInstance(b.foo[0], Foo)
            self.assertEqual(b.foo[0].a, 5)

        def test_dataclass_deserialization_with_generic_dict_type_hint(self):
            @dataclass
            class Foo:
                a: Any

            @dataclass
            class Bar:
                foo: Dict[int, Foo]

            b = deserialize({'foo': {0: {'a': 5}}}, Bar, globals=locals())
            self.assertIsInstance(b, Bar)
            self.assertIsInstance(b.foo, dict)
            self.assertEqual(1, len(b.foo))
            self.assertIsInstance(b.foo.get(0), Foo)
            self.assertEqual(b.foo[0].a, 5)

        def test_dataclass_deserialization_with_non_init_field(self):
            @dataclass
            class Foo:
                a: int
                b: str = field(init=False)

            f = deserialize({'a': 5, 'b': 'x'}, Foo, globals=locals())
            self.assertIsInstance(f, Foo)
            self.assertEqual(5, f.a)
            self.assertEqual('x', f.b)
