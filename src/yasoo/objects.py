from attr import attrs, attrib


@attrs
class DictWithSerializedKeys:
    data: dict = attrib()
    original_type: str = attrib()
