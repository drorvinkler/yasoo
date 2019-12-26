# yasoo
A python serializer of attrs and dataclass objects.

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
    def Foo(self: 'Foo'):
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
If you want to avoid having the `__type` key in your serialized data, you can set the `type_key` parameter to `False` when calling `serialize`.

For this to work all fields in the serialized class that are not json-serializable should have a type hint.
#### Multiple Serialization Methods For The Same Type
If you want to define a custom serialization method for a type for a specific use case, without affecting the default one, you can create another instance of `Serializer` and register this method om that instance. For example:
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
