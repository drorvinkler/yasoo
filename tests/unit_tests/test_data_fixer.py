from unittest import TestCase

from yasoo import serialize, deserialize, serializer
from yasoo.data_fixer import remove_type_data, rename_types


class TestDataFixer(TestCase):
    def test_remove_types(self):
        original = {'a': 1}
        type_key = '__type'
        data = serialize(original, type_key=type_key)
        restored = deserialize(data, obj_type=dict, type_key=None)
        self.assertIsInstance(restored, dict)
        self.assertNotEqual(original, restored)

        remove_type_data(data, type_key=type_key)
        restored = deserialize(data, obj_type=dict, type_key=None)
        self.assertIsInstance(restored, dict)
        self.assertEqual(original, restored)

    def test_rename_types(self):
        original = {'a': 1}
        type_key = '__type'

        class Foo:
            @staticmethod
            @serializer
            def serialize(_: 'Foo'):
                return dict(original)

        data = serialize(Foo(), type_key=type_key, fully_qualified_types=False, globals=locals())
        with self.assertRaises(TypeError):
            deserialize(dict(data), globals=locals())
        rename_types(data, type_key, {'Foo': 'builtins.dict'})
        restored = deserialize(data, type_key=type_key)
        self.assertEqual(original, restored)
