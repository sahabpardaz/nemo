import logging
from typing import Optional, TypeVar

from django.conf import settings
from django.core.cache import caches

from apps.utils.key_value_storage.key_value_storage import KeyValueStorage

TValue = TypeVar('TValue')

logger = logging.getLogger(__name__)


class CacheStorage(KeyValueStorage[str, TValue]):
    KEYS_PREFIX = "CacheStorage:"

    def __init__(self, cache_name: str = settings.CACHE_NAME_DEFAULT) -> None:
        super().__init__()
        self.cache = caches[cache_name]

    def put(self, key: str, value: TValue) -> None:
        self.cache.set(f"{CacheStorage.KEYS_PREFIX}{key}", value)

    def get(self, key: str) -> Optional[TValue]:
        try:
            return self.cache.get(f"{CacheStorage.KEYS_PREFIX}{key}")
        except ModuleNotFoundError as e:
            logger.error(f"CacheStorage.get error: It seems the name or location of {TValue} has been changed recently."
                         "If this is the case, just skip this error. "
                         "Otherwise, or if this error is seen again in the future, check the error details.\n"
                         f"Error message: {str(e)}")
            return None
