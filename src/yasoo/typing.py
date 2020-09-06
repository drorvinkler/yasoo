from typing import TypeVar, Type, Callable, overload, List, Set, Tuple, Dict

K = TypeVar("K")
V = TypeVar("V")


class List_:
    @overload
    def __class_getitem__(cls, item: Type[V]) -> Callable[[], List[V]]:
        ...

    def __class_getitem__(cls, item: Callable[[], V]) -> Callable[[], List[V]]:
        return List[item]


class Set_:
    @overload
    def __class_getitem__(cls, item: Type[V]) -> Callable[[], Set[V]]:
        ...

    def __class_getitem__(cls, item: Callable[[], V]) -> Callable[[], Set[V]]:
        return Set[item]


class Dict_:
    @overload
    def __class_getitem__(
        cls, item: Tuple[Type[K], Type[V]]
    ) -> Callable[[], Dict[K, V]]:
        ...

    @overload
    def __class_getitem__(
        cls, item: Tuple[Type[K], Callable[[], V]]
    ) -> Callable[[], Dict[K, V]]:
        ...

    @overload
    def __class_getitem__(
        cls, item: Tuple[Callable[[], K], Type[V]]
    ) -> Callable[[], Dict[K, V]]:
        ...

    def __class_getitem__(
        cls, item: Tuple[Callable[[], K], Callable[[], V]]
    ) -> Callable[[], Dict[K, V]]:
        return Dict[item[0], item[1]]
