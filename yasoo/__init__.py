from yasoo.deserialization import Deserializer
from yasoo.serialization import Serializer

_default_serializer = Serializer()
serialize = _default_serializer.serialize
register_serializer = _default_serializer.register()
register_serializer_for_type = _default_serializer.register

_default_deserializer = Deserializer()
deserialize = _default_deserializer.deserialize
register_deserializer = _default_deserializer.register()
register_deserializer_for_type = _default_deserializer.register
