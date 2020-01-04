import json
import logging
from unittest import TestCase

from attr import attrs, attrib
from attr.validators import instance_of
from yasoo import serialize
from yasoo.serialization import _logger


class TestAttrsSerialization(TestCase):
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
        self.assertEqual(f'{Foo.__module__}.{Foo.__name__}', s.get('__type'))

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

    def test_attr_warning_on_exception_in_converter(self):
        @attrs
        class Foo:
            bar = attrib(converter=lambda x: 1 / x)

        f = Foo(5)
        f.bar = 0
        with self.assertLogs(_logger.name, logging.WARNING) as cm:
            serialize(f)
        self.assertEqual(1, len(cm.records))
        self.assertEqual(logging.WARNING, cm.records[0].levelno)
        self.assertIn('value', cm.records[0].msg)
