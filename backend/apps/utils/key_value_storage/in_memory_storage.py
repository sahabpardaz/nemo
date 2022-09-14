from typing import Optional, TypeVar
from apps.utils.key_value_storage import KeyValueStorage

TKey = TypeVar('TKey')
TValue = TypeVar('TValue')


class InMemoryStorage(KeyValueStorage[TKey, TValue]):
    def __init__(self) -> None:
        self._data = {}

    def put(self, key: TKey, value: TValue) -> None:
        self._data[key] = value

    def get(self, key: TKey) -> Optional[TValue]:
        return self._data.get(key)
