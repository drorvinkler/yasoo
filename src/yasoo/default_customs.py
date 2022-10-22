from datetime import date, time, datetime

from .utils import type_to_string, fully_qualified_string_to_type


def serialize_date(d: date) -> dict:
    return {"date": d.toordinal()}


def deserialize_date(d: dict) -> date:
    return date.fromordinal(d["date"])


def serialize_time(t: time) -> dict:
    return {"time": t.isoformat()}


def deserialize_time(d: dict) -> time:
    return _time_from_iso_format(d["time"])


def serialize_datetime(d: datetime) -> dict:
    return {"time": d.timestamp()}


def deserialize_datetime(d: dict) -> datetime:
    return datetime.fromtimestamp(d["time"])


def serialize_type(obj: type) -> dict:
    return {"fully_qualified_name": type_to_string(obj, fully_qualified=True)}


def deserialize_type(data: dict, _) -> type:
    return fully_qualified_string_to_type(data["fully_qualified_name"])


def _time_from_iso_format_manually(s: str) -> time:
    if "." not in s:
        return datetime.strptime(s, "%H:%M:%S").time()
    return datetime.strptime(s, "%H:%M:%S.%f").time()


_time_from_iso_format = (
    time.fromisoformat
    if hasattr(time, "fromisoformat")
    else _time_from_iso_format_manually
)
