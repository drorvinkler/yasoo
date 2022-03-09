Changelog
=========
0.12.4 (2022-03-09)
___________________
- Supporting deserialization of classes with fields with ``init=False``.

0.12.3 (2022-01-11)
___________________
- If a deserialization method's forward reference is not found in globals, it will be searched for again every deserialization until it is found.

0.12.2 (2021-11-15)
___________________
- If globals are passed to ``deserialize``, they are enriched with classes encountered during deserialization.

0.12.1 (2021-10-31)
___________________
- Supporting deserialization of lists with generic type hints if the actual type was serialized.

0.12.0 (2021-10-28)
___________________
- Enums are now serialized by name, not by value.
- Enum deserialization falls back to value lookup, for backwards compatibility.

0.11.0 (2021-10-16)
___________________
- Enabled ignoring the custom deserializer of just the outermost object.

0.10.0 (2021-10-06)
___________________
- Allowing temporary de-registration of (de)serializers.
- When deserializing, can ignore extra fields instead of failing.

0.9.4 (2021-10-06)
___________________
- Supporting forward references in type hints.

0.9.3 (2021-09-02)
___________________
- Improved performance using caching.

0.9.2 (2021-08-02)
___________________
- Fixed a bug where deserialization of an iterable with a type hint could cause ``None`` values to be added to the iterable.

0.9.1 (2021-07-28)
___________________
- Added a default (de)serializer for ``type`` objects.
- Changed how the default (de)serializer of ``datetime`` is registered, to enable it for all (de)serializers.

0.9.0 (2021-07-22)
___________________
- Supporting registering custom (de)serializers for a class and all its descendants.

0.8.6 (2021-07-01)
___________________
- Added a default (de)serializer for ``datetime`` objects.

0.8.5 (2020-12-05)
-------------------
- Added data manipulation utils under ``yasoo.data_fixer``.

0.8.0 (2020-12-05)
-------------------
- Serializing ``dict`` keys that are not strings (can be overridden).
- Multiple bug fixes regarding mappings that are not ``dict``.

0.7.0 (2020-10-07)
-------------------
- Support for Python 3.9 (PEP 585).

0.6.1 (2020-09-06)
-------------------
- Hack to support deserialization with ``obj_type`` that is a generic type.

0.6.0 (2020-09-06)
-------------------
- Supporting tuples with mixed types without type key.

0.5.0 (2020-08-01)
-------------------
- Supporting complex keys in dictionaries, i.e. dataclasses, tuples etc.

0.4.0 (2020-05-08)
-------------------
- Supporting preservation of iterable types even when ``type_key`` is ``None``, through type hints.
- Changed all warnings to use ``warnings`` instead of ``logging``.
