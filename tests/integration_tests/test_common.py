from typing import Dict, Any
from unittest import TestCase

from yasoo import serialize, deserialize

from tests.test_classes import MyMapping


class TestCommon(TestCase):
    def test_dict_as_value_with_any_type_hint(self):
        data = {'a': {'b': 1}}
        serialized = serialize(data, type_key=None)
        self.assertRaises(ValueError, deserialize, serialized, obj_type=Dict[str, Any])

    def test_custom_mapping_with_serialized_keys(self):
        mapping = MyMapping({('a', 'b'): 1})
        restored = deserialize(serialize(mapping))
        self.assertIsInstance(restored, MyMapping)
        self.assertEqual(mapping, restored)

    def test_stringified_dict_key_types(self):
        original = {'a': 1, 2: 'b', True: 3}
        serialized = serialize(original, stringify_dict_keys=True)

        self.assertIsInstance(serialized, dict)
        for k in serialized.keys():
            self.assertIsInstance(k, str)

        restored = deserialize(serialized)
        self.assertEqual(original, restored)
