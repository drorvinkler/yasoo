from datetime import datetime, time

from .utils import type_to_string, fully_qualified_string_to_type


def serialize_time(t: time) -> dict:
    return {"time": t.isoformat()}


def deserialize_time(d: dict) -> time:
    return time.fromisoformat(d["time"])


def serialize_datetime(d: datetime) -> dict:
    return {"time": d.timestamp()}


def deserialize_datetime(d: dict) -> datetime:
    return datetime.fromtimestamp(d["time"])


def serialize_type(obj: type) -> dict:
    return {"fully_qualified_name": type_to_string(obj, fully_qualified=True)}


def deserialize_type(data: dict, _) -> type:
    return fully_qualified_string_to_type(data["fully_qualified_name"])
