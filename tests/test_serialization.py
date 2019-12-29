import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any
from unittest import TestCase

from attr import attrs, attrib
from attr.validators import instance_of

from yasoo import serialize, serializer, serializer_of
from yasoo.constants import ENUM_VALUE_KEY
from yasoo.serialization import _logger


class SerializationTests(TestCase):
    def test_attr_serialization_json_serializable(self):
        @attrs
        class Foo:
            a = attrib(default='a')

        @attrs
        class Bar:
            foo = attrib()
            bar = attrib(default=None)

        s = serialize(Bar(Foo({'a'})))
        try:
            json.dumps(s)
        except:
            self.fail('Serialized attrs object cannot be json dumped')

    def test_all_attr_fields_are_serialized(self):
        @attrs
        class Foo:
            a = attrib(default=None)
            bar = attrib(default=None)

        s = serialize(Foo())
        self.assertTrue('a' in s)
        self.assertTrue('bar' in s)

    def test_attr_serialization_of_type_info(self):
        @attrs
        class Foo:
            pass

        s = serialize(Foo(), type_key='__type', fully_qualified_types=False)
        self.assertEqual(Foo.__name__, s.get('__type'))

        s = serialize(Foo(), type_key='__type', fully_qualified_types=True)
        self.assertEqual('{}.{}'.format(Foo.__module__, Foo.__name__), s.get('__type'))

    def test_attr_warning_on_validator_mismatch(self):
        @attrs
        class Foo:
            bar = attrib(validator=instance_of(int))

        f = Foo(5)
        f.bar = 'a'
        with self.assertLogs(_logger.name, logging.WARNING) as cm:
            serialize(f)
        self.assertEqual(1, len(cm.records))
        self.assertEqual(logging.WARNING, cm.records[0].levelno)

    def test_attr_warning_on_validator_mismatch_with_converter(self):
        @attrs
        class Foo:
            bar = attrib(validator=instance_of(int), converter=lambda x: x)

        f = Foo(5)
        f.bar = 'a'
        with self.assertLogs(_logger.name, logging.WARNING) as cm:
            serialize(f)
        self.assertEqual(1, len(cm.records))
        self.assertEqual(logging.WARNING, cm.records[0].levelno)
        self.assertTrue('validator' in cm.records[0].msg)

    def test_attr_warning_on_converter(self):
        @attrs
        class Foo:
            bar = attrib(converter=lambda x: x)

        with self.assertLogs(_logger.name, logging.WARNING) as cm:
            serialize(Foo(5))
        self.assertEqual(1, len(cm.records))
        self.assertEqual(logging.WARNING, cm.records[0].levelno)

    def test_attr_warning_on_converter_validator_valid(self):
        @attrs
        class Foo:
            bar = attrib(validator=instance_of(int), converter=lambda x: x)

        with self.assertLogs(_logger.name, logging.WARNING) as cm:
            serialize(Foo(5))
        self.assertEqual(1, len(cm.records))
        self.assertEqual(logging.WARNING, cm.records[0].levelno)

    def test_attr_no_warning_on_validator_mismatch_for_complex_value(self):
        @attrs
        class Foo:
            a = attrib()

        @attrs
        class Bar:
            foo = attrib(validator=instance_of(Foo))

        try:
            with self.assertLogs(_logger.name, logging.WARNING):
                serialize(Bar(Foo(5)))
        except AssertionError:
            return
        self.fail()

    def test_dataclass_serialization_json_serializable(self):
        @dataclass
        class Foo:
            a: Any = 'a'

        @dataclass
        class Bar:
            foo: Any
            bar: Any = None

        s = serialize(Bar(Foo({'a'})))
        try:
            json.dumps(s)
        except:
            self.fail('Serialized attrs object cannot be json dumped')

    def test_all_dataclass_fields_are_serialized(self):
        @dataclass
        class Foo:
            a: Any = None
            bar: Any = None

        s = serialize(Foo())
        self.assertTrue('a' in s)
        self.assertTrue('bar' in s)

    def test_dataclass_serialization_of_type_info(self):
        @dataclass
        class Foo:
            pass

        s = serialize(Foo(), type_key='__type', fully_qualified_types=False)
        self.assertEqual(Foo.__name__, s.get('__type'))

        s = serialize(Foo(), type_key='__type', fully_qualified_types=True)
        self.assertEqual('{}.{}'.format(Foo.__module__, Foo.__name__), s.get('__type'))

    def test_enum_serialization(self):
        class Foo(Enum):
            A = 5
            B = 89

        @attrs
        class Bar:
            foo = attrib()

        s = serialize(Bar(Foo.A))
        self.assertEqual(Foo.A.value, s['foo'][ENUM_VALUE_KEY])

    def test_serializer_registration(self):
        class Foo:
            pass

        @serializer_of(Foo)
        def func(foo):
            return {'foo': 'bar'}

        s = serialize(Foo())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_static_method(self):
        class Foo:
            pass

        class Bar:
            @serializer_of(Foo)
            @staticmethod
            def func(foo):
                return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_forward_ref(self):
        class Foo:
            @staticmethod
            @serializer_of('Foo')
            def func(foo):
                return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_type_hint(self):
        class Foo:
            pass

        @serializer
        def func(foo: Foo):
            return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')

    def test_serializer_registration_type_hint_forward_ref(self):
        class Foo:
            @staticmethod
            @serializer
            def func(foo: 'Foo'):
                return {'foo': 'bar'}

        s = serialize(Foo(), globals=locals())
        self.assertEqual(s.get('foo'), 'bar')
