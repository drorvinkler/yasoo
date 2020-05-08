import json
from unittest import TestCase

from attr import attrs, attrib
from attr.validators import instance_of
from yasoo import serialize


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
        with self.assertWarnsRegex(RuntimeWarning, expected_regex='.*validator.*'):
            serialize(f)

    def test_attr_warning_on_validator_mismatch_with_converter(self):
        @attrs
        class Foo:
            bar = attrib(validator=instance_of(int), converter=lambda x: x)

        f = Foo(5)
        f.bar = 'a'
        with self.assertWarnsRegex(RuntimeWarning, expected_regex='.*validator.*'):
            serialize(f)

    def test_attr_warning_on_converter(self):
        @attrs
        class Foo:
            bar = attrib(converter=lambda x: x)

        with self.assertWarnsRegex(RuntimeWarning, expected_regex='.*converter.*'):
            serialize(Foo(5))

    def test_attr_warning_on_converter_validator_valid(self):
        @attrs
        class Foo:
            bar = attrib(validator=instance_of(int), converter=lambda x: x)

        with self.assertWarnsRegex(RuntimeWarning, expected_regex='.*converter.*'):
            serialize(Foo(5))

    def test_attr_no_warning_on_validator_mismatch_for_complex_value(self):
        @attrs
        class Foo:
            a = attrib()

        @attrs
        class Bar:
            foo = attrib(validator=instance_of(Foo))

        try:
            with self.assertWarns(Warning):
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
        with self.assertWarnsRegex(RuntimeWarning, expected_regex='.*value.*'):
            serialize(f)

    def test_attr_warning_on_dict_without_type_hint_and_no_type_key(self):
        @attrs
        class Foo:
            bar = attrib()

        f = Foo({1: 5})
        with self.assertWarnsRegex(RuntimeWarning, expected_regex='.*no type hint.*'):
            serialize(f, type_key=None)

    def test_attr_warning_on_dict_with_unsupported_type_hint_and_no_type_key(self):
        class Unsupported:
            pass

        @attrs
        class Foo:
            bar = attrib(type=Unsupported)

        f = Foo({1: 5})
        with self.assertWarnsRegex(RuntimeWarning, expected_regex='.*unsupported class.*'):
            serialize(f, type_key=None)

    def test_attr_no_warning_on_dict_with_dict_type_hint_and_no_type_key(self):
        @attrs
        class Foo:
            bar = attrib(type=dict)

        f = Foo({1: 5})
        try:
            with self.assertWarns(Warning):
                serialize(f, type_key=None)
        except AssertionError:
            return
        self.fail()
