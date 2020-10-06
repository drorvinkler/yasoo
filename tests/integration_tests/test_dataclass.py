import sys
from typing import Any, Dict, Tuple, Iterable, Generic, TypeVar
from unittest import TestCase, skip

from yasoo import serialize, deserialize, deserializer, serializer
from yasoo.typing import List_, Set_, Dict_

from tests.test_classes import MyIterable, MyMapping

try:
    from dataclasses import dataclass, field

    DATACLASSES_EXIST = True
except ModuleNotFoundError:
    DATACLASSES_EXIST = False


def python_39_needed(func):
    if sys.version_info.minor < 9:
        return skip('Python verion > 3.9 needed for this test')(func)
    return func


if DATACLASSES_EXIST:
    class TestDataclass(TestCase):
        def test_dataclass_with_only_primitives_no_type_hints(self):
            @dataclass
            class Foo:
                i: Any
                f: Any
                s: Any
                b: Any
                n: Any

            f = Foo(i=1, f=.5, s='b', b=True, n=None)
            f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertEqual(f2, f)

            f2 = deserialize(serialize(f, type_key=None), obj_type=Foo)
            self.assertIsInstance(f2, Foo)
            self.assertEqual(f2, f)

        def test_dataclass_with_classes_no_type_hints(self):
            @dataclass
            class Foo:
                a: Any

            @dataclass
            class Bar:
                foo: Any

            f = Foo(a=5)
            b = Bar(f)
            b2 = deserialize(serialize(b, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(b2, Bar)
            self.assertIsInstance(b2.foo, Foo)
            self.assertEqual(f.a, b2.foo.a)

        def test_dataclass_with_classes_with_type_hints(self):
            @dataclass
            class Foo:
                a: Any

            @dataclass
            class Bar:
                foo: Foo

            f = Foo(a=5)
            b = Bar(f)
            b2 = deserialize(serialize(b, type_key=None), obj_type=Bar)
            self.assertIsInstance(b2.foo, Foo)
            self.assertEqual(f.a, b2.foo.a)

        def test_dataclass_with_classes_with_wrong_type_hints(self):
            @dataclass
            class Foo:
                a: Any

            @dataclass
            class FakeFoo:
                b: Any

            @dataclass
            class Bar:
                foo: FakeFoo

            f = Foo(a=5)
            b = Bar(f)
            b2 = deserialize(serialize(b, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(b2, Bar)
            self.assertIsInstance(b2.foo, Foo)
            self.assertEqual(f.a, b2.foo.a)

        def test_dataclass_with_list_of_primitives_without_type_hint(self):
            @dataclass
            class Foo:
                l: Any

            f = Foo([1, 'a', True, None])
            f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.l, list)
            self.assertEqual(f.l, f2.l)

        def test_dataclass_with_list_of_classes_without_type_hint(self):
            @dataclass
            class Foo:
                i: Any

            @dataclass
            class Bar:
                l: Any

            b = Bar([Foo(1), Foo(2)])
            b2 = deserialize(serialize(b, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(b2, Bar)
            self.assertIsInstance(b2.l, list)
            self.assertTrue(all(isinstance(f, Foo) for f in b2.l))
            self.assertEqual(b.l, b2.l)

        def test_dataclass_with_iterable_without_type_hint_without_preservation(self):
            @dataclass
            class Foo:
                s: Any

            f = Foo(MyIterable(10, 'a', True, None))
            f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=False), globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.s, list)
            self.assertEqual(set(f.s), set(f2.s))

        def test_dataclass_with_iterable_without_type_hint_with_preservation(self):
            @dataclass
            class Foo:
                s: Any

            f = Foo(MyIterable(10, 'a', True, None))
            g = dict(globals())
            g.update(locals())
            f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=True), globals=g)
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.s, MyIterable)
            self.assertEqual(list(f.s), list(f2.s))

        def test_dataclass_with_iterable_with_type_hint_with_preservation(self):
            @dataclass
            class Foo:
                s: MyIterable

            f = Foo(MyIterable(10, 'a', True, None))
            f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=True, type_key=None), obj_type=Foo)
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.s, MyIterable)
            self.assertEqual(list(f.s), list(f2.s))

        def test_dataclass_with_iterable_with_wrong_type_hint_with_preservation(self):
            @dataclass
            class Foo:
                s: list

            f = Foo(MyIterable(10, 'a', True, None))
            g = dict(globals())
            g.update(locals())
            f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=True), globals=g)
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.s, MyIterable)
            self.assertEqual(list(f.s), list(f2.s))

        def test_dataclass_with_dict_of_primitives_without_type_hint(self):
            @dataclass
            class Foo:
                d: Any

            f = Foo({0: 1, 1: 'a', 2: True, 3: None})
            f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, dict)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_dict_of_primitives_with_type_hint(self):
            @dataclass
            class Foo:
                d: Dict[int, Any]

            f = Foo({0: 1, 1: 'a', 2: True, 3: None})
            f2 = deserialize(serialize(f, fully_qualified_types=False, type_key=None), obj_type=Foo)
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, dict)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_dict_of_classes_without_type_hint(self):
            @dataclass
            class Foo:
                i: Any

            @dataclass
            class Bar:
                d: Any

            b = Bar({0: Foo(1), 1: Foo(2)})
            b2 = deserialize(serialize(b, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(b2, Bar)
            self.assertIsInstance(b2.d, dict)
            self.assertTrue(all(isinstance(f, Foo) for f in b2.d.values()))
            self.assertEqual(b.d, b2.d)

        def test_dataclass_with_mapping_without_type_hint(self):
            @dataclass
            class Foo:
                d: Any

            f = Foo(MyMapping({0: 10, 1: 'a', 2: True, 3: None}))
            g = dict(globals())
            g.update(locals())
            f2 = deserialize(serialize(f, fully_qualified_types=False), globals=g)
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, MyMapping)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_mapping_with_type_hint(self):
            @dataclass
            class Foo:
                d: MyMapping

            f = Foo(MyMapping({0: 10, 1: 'a', 2: True, 3: None}))
            f2 = deserialize(serialize(f, fully_qualified_types=False, type_key=None), obj_type=Foo)
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, MyMapping)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_mapping_with_wrong_type_hint(self):
            @dataclass
            class Foo:
                d: dict

            f = Foo(MyMapping({0: 10, 1: 'a', 2: True, 3: None}))
            g = dict(globals())
            g.update(locals())
            f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=True), globals=g)
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, MyMapping)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_dict_with_complex_keys(self):
            @dataclass
            class Foo:
                d: Any

            f = Foo({(i, i*2): i for i in range(5)})
            f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, dict)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_dict_with_dataclass_keys(self):
            @dataclass
            class Foo:
                d: Any

            @dataclass(frozen=True)
            class MyKey:
                k: Any

            f = Foo({MyKey(str(i)): i for i in range(5)})
            f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, dict)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_dict_with_complex_keys_and_type_hints(self):
            @dataclass
            class Foo:
                d: Dict[tuple, int]

            f = Foo({(i, i*2): i for i in range(5)})
            f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, dict)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_dict_with_complex_keys_and_complex_values(self):
            @dataclass
            class Bar:
                d: Any

            @dataclass
            class Foo:
                d: Any

            f = Foo({(i, i * 2): Bar(i) for i in range(5)})
            f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, dict)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_dict_with_complex_keys_and_complex_values_and_type_hints(self):
            @dataclass
            class Bar:
                b: int

            @dataclass
            class Foo:
                d: Dict[tuple, Bar]

            f = Foo({(i, i * 2): Bar(i) for i in range(5)})
            f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.d, dict)
            self.assertEqual(f.d, f2.d)

        def test_dataclass_with_mixed_tuple_of_primitives_and_type_hints(self):
            @dataclass
            class Foo:
                a: Tuple[int, str]

            f = Foo((8, 'dfkjh'))
            f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.a, Iterable)
            self.assertEqual(list(f.a), list(f2.a))

        def test_dataclass_with_mixed_tuple_and_type_hints(self):
            @dataclass
            class Bar:
                b: str

            @dataclass
            class Foo:
                a: Tuple[int, Bar]

            f = Foo((8, Bar('dfkjh')))
            f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.a, Iterable)
            self.assertEqual(list(f.a), list(f2.a))

        def test_dataclass_with_tuple_of_classes_and_type_hints(self):
            @dataclass
            class Bar:
                b: str

            @dataclass
            class Foo:
                a: Tuple[Bar, ...]

            f = Foo(tuple(Bar(str(i)) for i in range(5)))
            f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.a, Iterable)
            self.assertEqual(list(f.a), list(f2.a))

        def test_dataclass_with_user_defined_generic_class_and_type_hints(self):
            T = TypeVar('T')

            class MyGeneric(Generic[T]):
                pass

            @dataclass
            class Foo:
                a: MyGeneric[int]

            @serializer
            def sfunc(_: MyGeneric):
                return {}

            @deserializer
            def dfunc(_) -> MyGeneric:
                return MyGeneric()

            f = Foo(MyGeneric())
            f2 = deserialize(serialize(f, type_key=None), Foo, globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.a, MyGeneric)

        @python_39_needed
        def test_dataclass_with_generic_type_hint_in_list(self):
            @dataclass
            class Bar:
                b: int

            @dataclass
            class Foo:
                a: list[Bar]

            f = Foo([Bar(i) for i in range(5)])
            f2 = deserialize(serialize(f, type_key=None), Foo, globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.a, list)
            self.assertEqual(f.a, f2.a)

        @python_39_needed
        def test_dataclass_with_generic_type_hint_in_set_and_preservation(self):
            @dataclass
            class Foo:
                a: set[int]

            f = Foo(set(range(5)))
            f2 = deserialize(serialize(f, type_key=None, preserve_iterable_types=True), Foo, globals=locals())
            self.assertIsInstance(f2, Foo)
            self.assertIsInstance(f2.a, set)
            self.assertEqual(f.a, f2.a)

        def test_deserialization_with_yasoo_type_hints(self):
            @dataclass(frozen=True)
            class Foo:
                a: int

            l = [[Foo(i) for i in range(5)] for _ in range(5)]
            l2 = deserialize(serialize(l, type_key=None), obj_type=List_[List_[Foo]])
            self.assertIsInstance(l2, list)
            self.assertIsInstance(l2[0], list)
            self.assertIsInstance(l2[0][0], Foo)
            self.assertEqual(l, l2)

            l = [set(i) for i in l]
            l2 = deserialize(serialize(l, type_key=None), obj_type=List_[Set_[Foo]])
            self.assertIsInstance(l2, list)
            self.assertIsInstance(l2[0], list)
            self.assertIsInstance(l2[0][0], Foo)
            for i1, i2 in zip(l, l2):
                self.assertEqual(i1, set(i2))

            d = dict(enumerate(l))
            d2 = deserialize(serialize(d, type_key=None), obj_type=Dict_[int, Set_[Foo]])
            self.assertIsInstance(d2, dict)
            self.assertEqual(d.keys(), d2.keys())
            self.assertIsInstance(d2[0], list)
            self.assertIsInstance(d2[0][0], Foo)
            for k, v in d.items():
                self.assertEqual(v, set(d2[k]))
