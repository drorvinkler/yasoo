from attr import attrs, attrib


@attrs
class AttrsClass:
    pass


@attrs
class FooContainer:
    foo = attrib()
