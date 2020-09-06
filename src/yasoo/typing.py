from typing import TypeVar, Type, Callable, overload, List, Set, Tuple, Dict

K = TypeVar("K")
V = TypeVar("V")


class _List:
    @overload
    def __getitem__(self, item: Type[V]) -> Callable[[], List[V]]:
        ...

    def __getitem__(self, item: Callable[[], V]) -> Callable[[], List[V]]:
        return List[item]


class _Set:
    @overload
    def __getitem__(self, item: Type[V]) -> Callable[[], Set[V]]:
        ...

    def __getitem__(self, item: Callable[[], V]) -> Callable[[], Set[V]]:
        return Set[item]


class _Dict:
    @overload
    def __getitem__(self, item: Tuple[Type[K], Type[V]]) -> Callable[[], Dict[K, V]]:
        ...

    @overload
    def __getitem__(
        self, item: Tuple[Type[K], Callable[[], V]]
    ) -> Callable[[], Dict[K, V]]:
        ...

    @overload
    def __getitem__(
        self, item: Tuple[Callable[[], K], Type[V]]
    ) -> Callable[[], Dict[K, V]]:
        ...

    def __getitem__(
        self, item: Tuple[Callable[[], K], Callable[[], V]]
    ) -> Callable[[], Dict[K, V]]:
        return Dict[item[0], item[1]]


List_ = _List()
Set_ = _Set()
Dict_ = _Dict()
