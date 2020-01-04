import json
from typing import Any
from unittest import TestCase

from yasoo import serialize

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
