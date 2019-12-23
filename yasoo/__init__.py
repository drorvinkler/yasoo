from yasoo.deserialization import Deserializer
from yasoo.serialization import Serializer

_default_serializer = Serializer()
serialize = _default_serializer.serialize
serializer = _default_serializer.register()
serializer_of = _default_serializer.register

_default_deserializer = Deserializer()
deserialize = _default_deserializer.deserialize
deserializer = _default_deserializer.register()
deserializer_of = _default_deserializer.register
