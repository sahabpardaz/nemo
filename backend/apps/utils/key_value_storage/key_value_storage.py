from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

TKey = TypeVar('TKey')
TValue = TypeVar('TValue')


class KeyValueStorage(ABC, Generic[TKey, TValue]):
    @abstractmethod
    def put(self, key: TKey, value: TValue) -> None:
        pass

    @abstractmethod
    def get(self, key: TKey) -> Optional[TValue]:
        pass

    def has_key(self, key: TKey) -> bool:
        return self.get(key) is not None
