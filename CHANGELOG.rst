Changelog
=========
0.7.0 (2020-10-07)
-------------------
- Support for Python 3.9 (PEP 585).

0.6.1 (2020-09-06)
-------------------
- Hack to support deserialization with `obj_type` that is a generic type.

0.6.0 (2020-09-06)
-------------------
- Supporting tuples with mixed types without type key.

0.5.0 (2020-08-01)
-------------------
- Supporting complex keys in dictionaries, i.e. dataclasses, tuples etc.

0.4.0 (2020-05-08)
-------------------
- Supporting preservation of iterable types even when `type_key` is `None`, through type hints.
- Changed all warnings to use `warnings` instead of `logging`.
