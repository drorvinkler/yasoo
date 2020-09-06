from typing import Dict, Any, Tuple, Iterable
from unittest import TestCase

from attr import attrs, attrib
from yasoo import serialize, deserialize
from yasoo.typing import List_, Set_, Dict_

from tests.test_classes import MyIterable, MyMapping


class TestAttrs(TestCase):
    def test_attrs_with_only_primitives_no_type_hints(self):
        @attrs
        class Foo:
            i = attrib()
            f = attrib()
            s = attrib()
            b = attrib()
            n = attrib()

        f = Foo(i=1, f=.5, s='b', b=True, n=None)
        f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertEqual(f2, f)

        f2 = deserialize(serialize(f, type_key=None), obj_type=Foo)
        self.assertIsInstance(f2, Foo)
        self.assertEqual(f2, f)

    def test_attrs_with_classes_no_type_hints(self):
        @attrs
        class Foo:
            a = attrib()

        @attrs
        class Bar:
            foo = attrib()

        f = Foo(a=5)
        b = Bar(f)
        b2 = deserialize(serialize(b, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(b2, Bar)
        self.assertIsInstance(b2.foo, Foo)
        self.assertEqual(f.a, b2.foo.a)

    def test_attrs_with_classes_with_type_hints(self):
        @attrs
        class Foo:
            a = attrib()

        @attrs
        class Bar:
            foo: Foo = attrib()

        f = Foo(a=5)
        b = Bar(f)
        b2 = deserialize(serialize(b, type_key=None), obj_type=Bar)
        self.assertIsInstance(b2.foo, Foo)
        self.assertEqual(f.a, b2.foo.a)

    def test_attrs_with_classes_with_wrong_type_hints(self):
        @attrs
        class Foo:
            a = attrib()

        @attrs
        class FakeFoo:
            b = attrib()

        @attrs
        class Bar:
            foo: FakeFoo = attrib()

        f = Foo(a=5)
        b = Bar(f)
        b2 = deserialize(serialize(b, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(b2, Bar)
        self.assertIsInstance(b2.foo, Foo)
        self.assertEqual(f.a, b2.foo.a)

    def test_attrs_with_list_of_primitives_without_type_hint(self):
        @attrs
        class Foo:
            l = attrib()

        f = Foo([1, 'a', True, None])
        f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.l, list)
        self.assertEqual(f.l, f2.l)

    def test_attrs_with_list_of_classes_without_type_hint(self):
        @attrs
        class Foo:
            i = attrib()

        @attrs
        class Bar:
            l = attrib()

        b = Bar([Foo(1), Foo(2)])
        b2 = deserialize(serialize(b, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(b2, Bar)
        self.assertIsInstance(b2.l, list)
        self.assertTrue(all(isinstance(f, Foo) for f in b2.l))
        self.assertEqual(b.l, b2.l)

    def test_attrs_with_iterable_without_type_hint_without_preservation(self):
        @attrs
        class Foo:
            s = attrib()

        f = Foo(MyIterable(10, 'a', True, None))
        f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=False), globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.s, list)
        self.assertEqual(set(f.s), set(f2.s))

    def test_attrs_with_iterable_without_type_hint_with_preservation(self):
        @attrs
        class Foo:
            s = attrib()

        f = Foo(MyIterable(10, 'a', True, None))
        g = dict(globals())
        g.update(locals())
        f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=True), globals=g)
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.s, MyIterable)
        self.assertEqual(list(f.s), list(f2.s))

    def test_attrs_with_iterable_with_type_hint_with_preservation(self):
        @attrs
        class Foo:
            s: MyIterable = attrib()

        f = Foo(MyIterable(10, 'a', True, None))
        f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=True, type_key=None), obj_type=Foo)
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.s, MyIterable)
        self.assertEqual(list(f.s), list(f2.s))

    def test_attrs_with_iterable_with_wrong_type_hint_with_preservation(self):
        @attrs
        class Foo:
            s: list = attrib()

        f = Foo(MyIterable(10, 'a', True, None))
        g = dict(globals())
        g.update(locals())
        f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=True), globals=g)
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.s, MyIterable)
        self.assertEqual(list(f.s), list(f2.s))

    def test_attrs_with_dict_of_primitives_without_type_hint(self):
        @attrs
        class Foo:
            d = attrib()

        f = Foo({0: 1, 1: 'a', 2: True, 3: None})
        f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, dict)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_dict_of_primitives_with_type_hint(self):
        @attrs
        class Foo:
            d: Dict[int, Any] = attrib()

        f = Foo({0: 1, 1: 'a', 2: True, 3: None})
        f2 = deserialize(serialize(f, fully_qualified_types=False, type_key=None), obj_type=Foo)
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, dict)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_dict_of_classes_without_type_hint(self):
        @attrs
        class Foo:
            i = attrib()

        @attrs
        class Bar:
            d = attrib()

        b = Bar({0: Foo(1), 1: Foo(2)})
        b2 = deserialize(serialize(b, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(b2, Bar)
        self.assertIsInstance(b2.d, dict)
        self.assertTrue(all(isinstance(f, Foo) for f in b2.d.values()))
        self.assertEqual(b.d, b2.d)

    def test_attrs_with_mapping_without_type_hint(self):
        @attrs
        class Foo:
            d = attrib()

        f = Foo(MyMapping({0: 10, 1: 'a', 2: True, 3: None}))
        g = dict(globals())
        g.update(locals())
        f2 = deserialize(serialize(f, fully_qualified_types=False), globals=g)
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, MyMapping)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_mapping_with_type_hint(self):
        @attrs
        class Foo:
            d: MyMapping = attrib()

        f = Foo(MyMapping({0: 10, 1: 'a', 2: True, 3: None}))
        f2 = deserialize(serialize(f, fully_qualified_types=False, type_key=None), obj_type=Foo)
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, MyMapping)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_mapping_with_wrong_type_hint(self):
        @attrs
        class Foo:
            d: dict = attrib()

        f = Foo(MyMapping({0: 10, 1: 'a', 2: True, 3: None}))
        g = dict(globals())
        g.update(locals())
        f2 = deserialize(serialize(f, fully_qualified_types=False, preserve_iterable_types=True), globals=g)
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, MyMapping)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_dict_with_complex_keys(self):
        @attrs
        class Foo:
            d = attrib()

        f = Foo({(i, i * 2): i for i in range(5)})
        f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, dict)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_dict_with_attrs_keys(self):
        @attrs
        class Foo:
            d = attrib()

        @attrs(frozen=True)
        class MyKey:
            k = attrib()

        f = Foo({MyKey(str(i)): i for i in range(5)})
        f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, dict)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_dict_with_complex_keys_and_type_hints(self):
        @attrs
        class Foo:
            d: Dict[tuple, int] = attrib()

        f = Foo({(i, i * 2): i for i in range(5)})
        f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, dict)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_dict_with_complex_keys_and_complex_values(self):
        @attrs
        class Foo:
            d = attrib()

        @attrs
        class Bar:
            d = attrib()

        f = Foo({(i, i * 2): Bar(i) for i in range(5)})
        f2 = deserialize(serialize(f, fully_qualified_types=False), globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, dict)
        self.assertEqual(f.d, f2.d)

    def test_attrs_with_dict_with_complex_keys_and_complex_values_and_type_hints(self):
        @attrs
        class Bar:
            b: int = attrib()

        @attrs
        class Foo:
            d: Dict[tuple, Bar] = attrib()

        f = Foo({(i, i * 2): Bar(i) for i in range(5)})
        f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.d, dict)
        self.assertEqual(f.d, f2.d)

    def test_dataclass_with_mixed_tuple_of_primitives_and_type_hints(self):
        @attrs
        class Foo:
            a: Tuple[int, str] = attrib()

        f = Foo((8, 'dfkjh'))
        f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.a, Iterable)
        self.assertEqual(list(f.a), list(f2.a))

    def test_dataclass_with_mixed_tuple_and_type_hints(self):
        @attrs
        class Bar:
            b: str = attrib()

        @attrs
        class Foo:
            a: Tuple[int, Bar] = attrib()

        f = Foo((8, Bar('dfkjh')))
        f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.a, Iterable)
        self.assertEqual(list(f.a), list(f2.a))

    def test_dataclass_with_tuple_of_classes_and_type_hints(self):
        @attrs
        class Bar:
            b: str = attrib()

        @attrs
        class Foo:
            a: Tuple[Bar, ...] = attrib()

        f = Foo(tuple(Bar(str(i)) for i in range(5)))
        f2 = deserialize(serialize(f, type_key=None, fully_qualified_types=False), Foo, globals=locals())
        self.assertIsInstance(f2, Foo)
        self.assertIsInstance(f2.a, Iterable)
        self.assertEqual(list(f.a), list(f2.a))

    def test_deserialization_with_yasoo_type_hints(self):
        @attrs(frozen=True)
        class Foo:
            a: int = attrib()

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
