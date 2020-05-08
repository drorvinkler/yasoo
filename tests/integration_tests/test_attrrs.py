from unittest import TestCase

from attr import attrs, attrib
from yasoo import serialize, deserialize

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
