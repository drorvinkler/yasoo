from datetime import datetime
from enum import Enum
from typing import Sequence
from unittest import TestCase

from yasoo import serialize, serializer, serializer_of
from yasoo.constants import ENUM_VALUE_KEY, ITERABLE_VALUE_KEY

from tests.test_classes import FooContainer, MyMapping, MyIterable

_TYPE_KEY = '__type'


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

        s = serialize(Foo())
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

        s = serialize(Foo())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_type_hint_forward_ref(self):
        class Foo:
            @staticmethod
            @serializer
            def func(_: 'Foo'):
                return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_datetime_overrides_default(self):
        _dict = {'x': 1}

        @serializer_of(datetime)
        def foo(d: datetime) -> dict:
            return _dict

        self.assertEqual(_dict, serialize(datetime.now(), type_key=None))

    def test_serializer_registration_including_descendants(self):
        _dict = {'x': 1}

        class Foo:
            pass

        class Bar(Foo):
            pass

        @serializer_of(Foo, include_descendants=True)
        def foo(f: Foo) -> dict:
            return _dict

        self.assertEqual(_dict, serialize(Foo(), type_key=None))
        self.assertEqual(_dict, serialize(Bar(), type_key=None))

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
        s = serialize([Foo() for _ in range(list_len)],
                      type_key=type_key,
                      fully_qualified_types=False)
        self.assertIsInstance(s, list)
        self.assertEqual(list_len, len(s))
        for d in s:
            self.assertEqual({type_key: 'Foo'}, d)

    def test_serialization_of_dict(self):
        class Foo:
            pass

        @serializer
        def deserialize_foo(_: Foo):
            return {}

        type_key = '__type'
        d = {str(i): Foo() for i in range(5)}
        s = serialize(d,
                      type_key=type_key,
                      fully_qualified_types=False)
        self.assertIsInstance(s, dict)
        self.assertEqual('dict', s.get(type_key))
        s.pop(type_key)
        self.assertEqual(len(d), len(s))
        for key in d.keys():
            self.assertEqual({type_key: 'Foo'}, s.get(key))

    def test_serialization_of_inner_list_of_primitives_without_preservation(self):
        self._check_serialization_of_inner_iterable_of_primitives(list, False)

    def test_serialization_of_inner_iterable_of_primitives_without_preservation(self):
        self._check_serialization_of_inner_iterable_of_primitives(MyIterable, False)

    def test_serialization_of_inner_list_of_primitives_with_preservation(self):
        self._check_serialization_of_inner_iterable_of_primitives(list, True)

    def test_serialization_of_inner_iterable_of_primitives_with_preservation(self):
        self._check_serialization_of_inner_iterable_of_primitives(MyIterable, True)

    def test_serialization_of_inner_list_of_classes(self):
        self._check_serialization_of_inner_iterable_of_classes(list)

    def test_serialization_of_inner_iterable_of_classes(self):
        self._check_serialization_of_inner_iterable_of_classes(MyIterable)

    def test_serialization_of_inner_dict_of_primitives(self):
        self._check_serialization_of_inner_mapping_of_primitives(dict)

    def test_serialization_of_inner_custom_mapping_of_primitives(self):
        self._check_serialization_of_inner_mapping_of_primitives(MyMapping)

    def test_serialization_of_inner_dict_of_classes(self):
        self._check_serialization_of_inner_mapping_of_classes(dict)

    def test_serialization_of_inner_custom_mapping_of_classes(self):
        self._check_serialization_of_inner_mapping_of_classes(MyMapping)

    def test_serialization_inner_dict_with_invalid_keys(self):
        class Foo:
            pass

        d = {Foo(): 0}
        self.assertRaises(ValueError,
                          serialize,
                          obj=FooContainer(foo=d))

    def _check_serialization_of_inner_iterable_of_primitives(self, iterable_type, preserve_iterable_types):
        self._check_serialization_of_inner_iterable_of_primitives_with_given_type_key(iterable_type, preserve_iterable_types, _TYPE_KEY)
        self._check_serialization_of_inner_iterable_of_primitives_with_given_type_key(iterable_type, preserve_iterable_types, None)

    def _check_serialization_of_inner_iterable_of_classes(self, iterable_type):
        self._check_serialization_of_inner_iterable_of_classes_with_given_type_key(iterable_type, _TYPE_KEY)
        self._check_serialization_of_inner_iterable_of_classes_with_given_type_key(iterable_type, None)

    def _check_serialization_of_inner_iterable_of_primitives_with_given_type_key(self, iterable_type, preserve_iterable_types, type_key):
        size = 5
        it = iterable_type(range(size))
        s = serialize(FooContainer(foo=it),
                      type_key=type_key,
                      fully_qualified_types=False,
                      preserve_iterable_types=preserve_iterable_types)
        self.assertIsInstance(s, dict)
        self.assertIn('foo', s)

        foo = s['foo']
        if preserve_iterable_types and iterable_type != list:
            self.assertIsInstance(foo, dict)
            if type_key is not None:
                self.assertEqual(iterable_type.__name__, foo.get(type_key))
            foo = foo.get(ITERABLE_VALUE_KEY)

        self.assertIsInstance(foo, list)
        self.assertEqual(size, len(foo))
        if issubclass(iterable_type, Sequence):
            self.assertEqual(list(it), list(foo))
        else:
            self.assertEqual(set(it), set(foo))

    def _check_serialization_of_inner_iterable_of_classes_with_given_type_key(self, iterable_type, type_key):
        class Foo:
            pass

        @serializer
        def deserialize_foo(_: Foo):
            return {}

        size = 5
        it = iterable_type(Foo() for _ in range(size))
        s = serialize(FooContainer(foo=it),
                      type_key=type_key,
                      fully_qualified_types=False)
        self.assertIsInstance(s, dict)
        self.assertIn('foo', s)

        foo = s['foo']
        self.assertIsInstance(foo, list)
        self.assertEqual(size, len(foo))
        if type_key is not None:
            for d in foo:
                self.assertEqual({type_key: 'Foo'}, d)

    def _check_serialization_of_inner_mapping_of_primitives(self, mapping_type):
        m = mapping_type({str(i): i**2 for i in range(5)})
        s = serialize(FooContainer(foo=m),
                      type_key=_TYPE_KEY,
                      fully_qualified_types=False)
        self.assertIsInstance(s, dict)
        self.assertIn('foo', s)

        foo = s['foo']
        self.assertIsInstance(foo, dict)
        self.assertEqual(mapping_type.__name__, foo.get(_TYPE_KEY))
        foo.pop(_TYPE_KEY)
        self.assertEqual(dict(m), foo)

    def _check_serialization_of_inner_mapping_of_classes(self, mapping_type):
        class Foo:
            pass

        @serializer
        def serialize_foo(_: Foo):
            return {}

        m = mapping_type({str(i): Foo() for i in range(5)})
        s = serialize(FooContainer(foo=m),
                      type_key=_TYPE_KEY,
                      fully_qualified_types=False)
        self.assertIsInstance(s, dict)
        self.assertIn('foo', s)

        foo = s['foo']
        self.assertIsInstance(foo, dict)
        self.assertEqual(mapping_type.__name__, foo.get(_TYPE_KEY))
        foo.pop(_TYPE_KEY)
        self.assertEqual(len(m), len(foo))
        for key in m.keys():
            self.assertEqual({_TYPE_KEY: 'Foo'}, foo.get(key))
