from unittest import TestCase

from yasoo import deserialize, deserializer_of, deserializer


class TestSerializationCommon(TestCase):
    def test_deserialization_unknown_type_raises_error(self):
        self.assertRaises(ValueError, deserialize, {})

    def test_deserializer_registration(self):
        class Foo:
            pass

        @deserializer_of(Foo)
        def func(_):
            return Foo()

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_static_method(self):
        class Foo:
            pass

        class Bar:
            # noinspection PyNestedDecorators
            @deserializer_of(Foo)
            @staticmethod
            def func(_):
                return Foo()

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_forward_ref(self):
        class Foo:
            pass

            @staticmethod
            @deserializer_of('Foo')
            def func(_):
                return Foo()

        f = deserialize({}, Foo, globals=locals())
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_type_hint(self):
        class Foo:
            pass

        @deserializer
        def func(_) -> Foo:
            return Foo()

        f = deserialize({}, Foo)
        self.assertEqual(Foo, type(f))

    def test_deserializer_registration_type_hint_forward_ref(self):
        class Foo:
            pass

            @staticmethod
            @deserializer
            def func(_) -> 'Foo':
                return Foo()

        f = deserialize({}, Foo, globals=locals())
        self.assertEqual(Foo, type(f))
