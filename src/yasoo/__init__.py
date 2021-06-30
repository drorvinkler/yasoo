from datetime import datetime

from .deserialization import Deserializer
from .serialization import Serializer

_default_serializer = Serializer()
serialize = _default_serializer.serialize
serializer = _default_serializer.register()
serializer_of = _default_serializer.register

_default_deserializer = Deserializer()
deserialize = _default_deserializer.deserialize
deserializer = _default_deserializer.register()
deserializer_of = _default_deserializer.register


@serializer_of(datetime)
def _serialize_datetime(d: datetime) -> dict:
    return {"time": d.timestamp()}


@deserializer_of(datetime)
def _deserialize_datetime(d: dict) -> datetime:
    return datetime.fromtimestamp(d["time"])
