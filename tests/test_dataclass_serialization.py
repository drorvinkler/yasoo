import json
import logging
from typing import Any
from unittest import TestCase

from yasoo import serialize
from yasoo.serialization import _logger

try:
    from dataclasses import dataclass, field

    DATACLASSES_EXIST = True
except ModuleNotFoundError:
    DATACLASSES_EXIST = False


if DATACLASSES_EXIST:
    class TestDataclassSerialization(TestCase):
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
            self.assertEqual(f'{Foo.__module__}.{Foo.__name__}', s.get('__type'))

        def test_dataclass_warning_on_dict_without_type_hint_and_no_type_key(self):
            @dataclass
            class Foo:
                bar: Any

            f = Foo({1: 5})
            with self.assertLogs(_logger.name, logging.WARNING) as cm:
                serialize(f, type_key=None)
            self.assertEqual(1, len(cm.records))
            self.assertEqual(logging.WARNING, cm.records[0].levelno)
            self.assertIn('no type hint', cm.records[0].msg)

        def test_dataclass_warning_on_dict_with_unsupported_type_hint_and_no_type_key(self):
            class Unsupported:
                pass

            @dataclass
            class Foo:
                bar: Unsupported

            f = Foo({1: 5})
            with self.assertLogs(_logger.name, logging.WARNING) as cm:
                serialize(f, type_key=None)
            self.assertEqual(1, len(cm.records))
            self.assertEqual(logging.WARNING, cm.records[0].levelno)
            self.assertIn('unsupported', cm.records[0].msg)

        def test_dataclass_no_warning_on_dict_with_dict_type_hint_and_no_type_key(self):
            @dataclass
            class Foo:
                bar: dict

            f = Foo({1: 5})
            try:
                with self.assertLogs(_logger.name, logging.WARNING) as cm:
                    serialize(f, type_key=None)
            except AssertionError:
                return
            self.fail()
