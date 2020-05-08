# `yasoo`: Serialize the Data You Have

[![Build Status](https://travis-ci.com/drorvinkler/yasoo.svg?branch=master)](https://travis-ci.com/drorvinkler/yasoo)
[![codecov](https://codecov.io/gh/drorvinkler/yasoo/branch/master/graph/badge.svg)](https://codecov.io/gh/drorvinkler/yasoo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A python serializer of `attrs` and `dataclass` objects that doesn't rely on type hints.

## Why yasoo
`yasoo` adds type data to the serialized data, so deserialization doesn't need to rely on type hints.

Moreover, if you have a field that can contain multiple types of values, or a field which contains some specific implementation of an abstract class, `yasoo` has no problem with that.

For example, this code works fine:
```
from attr import attrs, attrib
from yasoo import serialize, deserialize

@attrs
class Foo:
    a = attrib()

@attrs
class Bar:
    foo: Foo = attrib()

serialized = serialize(Bar(foo=5))
assert(deserialize(serialized).foo == 5)
```

## Usage
### Basic Usage
For simple objects, use:
```
from yasoo import serialize, deserialize

with open(path, 'w') as f:
    json.dump(serialize(obj), f)

with open(path) as f:
    obj = deserizlie(json.load(f))
```
### Advanced Usage
#### Custom (De)Serializers
For objects that need custom serialization/deserialization, you can register your own methods:
```
from attr import attrs, attrib, asdict
from yasoo import serialize, deserialize, serializer, deserializer

@attrs
class Foo:
    bar = attrib(converter=lambda x: x * 2)

    def set_foobar(self, foobar):
        self.foobar = foobar

    @serializer
    def serialize(self: 'Foo'):
        result = asdict(self)
        if hasattr(self, 'foobar'):
            result['foobar'] = self.foobar
        return result

    @staticmethod
    @deserializer
    def deserialize(data: dict) -> 'Foo':
        foo = Foo(data['bar'] / 2)
        if 'foobar' in data:
            foo.set_foobar(data['foobar'])
        return foo
```
Notice that registering custom methods with forward reference (i.e. `'Foo'` instead of `Foo`) requires passing the `globals` parameter to `serialize`/`deserialize`, e.g.
```
serialize(obj, globals=globals())
```
#### Using Type Hints
If you want to avoid having the `__type` key in your serialized data, you can set the `type_key` parameter to `None` when calling `serialize`.

For this to work all fields in the serialized class that are not json-serializable should have a type hint.
#### Serializing Sequences
By default all sequences found in the data will be converted to `list` in the serialization process.
If you want to be able to deserialize them back to anything other than a list, set the `preserve_iterable_types` parameter to `True` when calling `serialize`.

Note: setting the `preserve_iterable_types` parameter to `True` will cause all iterables that are not `list` to be serialized as dictionaries with their type saved under the `type_key`.
#### Multiple Serialization Methods For The Same Type
If you want to define a custom serialization method for a type for a specific use case, without affecting the default serializer, you can create another instance of `Serializer` and register the method on that instance. For example:
```
from yasoo import Serializer, serializer, serialize

@serializer
def serialize_foo(foo: Foo):
    return {'bar': foo.bar}

my_serializer = Serializer()

@my_serializer.register()
def serialize_foo_another_way(foo: Foo):
    return {'bar': foo.bar * 2}

serialize(Foo(bar=5))  # returns {'bar': 5, '__type': 'Foo'}
my_serializer.serialize(Foo(bar=5))  # returns {'bar': 10, '__type': 'Foo'}
```
