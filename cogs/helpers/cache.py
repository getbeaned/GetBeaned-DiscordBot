import collections
import time
import typing
from typing import Dict, Callable


class CacheStorageDict(collections.MutableMapping):
    def __init__(self, expire_after: float = 60, strict: bool = False, default: Callable = None, *args, **kwargs):
        self.store = dict()
        self.times = dict()
        self.expire_after = expire_after
        self.strict = strict
        self.default_func = default
        self.update(dict(*args, **kwargs))  # use the free update to set keys
        self._expired_keys = 0
        self.hits = 0
        self.misses = 0

    def get(self, key: typing.Hashable, default: typing.Any = None):
        try:
            r = self[key]
            if r is None:
                return default
            else:
                return r
        except KeyError:
            return default

    def reset_expiry(self, key: typing.Hashable, seconds: float = None):
        if seconds is None:
            self.times[key] = time.time() + self.expire_after
        else:
            self.times[key] = time.time() + seconds

    def cleanup(self) -> int:
        i = 0
        for key, expire in list(self.times.items()):
            if time.time() > expire:
                i += 1
                del self[key]

        self._expired_keys += i
        return i

    def get_status(self) -> typing.Dict[str, int]:
        status_dict = {
            "expired_keys": set(),
            "stored_keys_count": 0,
            "stored_expired_keys_count": 0,
            "expired_keys_count": 0,
            "hits": self.hits,
            "misses": self.misses,
        }

        for key, expire in self.times.items():
            if time.time() > expire:
                status_dict["expired_keys"].add(key)

        status_dict["stored_keys_count"] = len(self.store)
        status_dict["stored_expired_keys_count"] = len(status_dict["expired_keys"])
        status_dict["expired_keys_count"] = self._expired_keys + len(status_dict["expired_keys"])

        return status_dict

    def __getitem__(self, key: typing.Hashable):
        if key not in self.store:
            self.misses += 1
            if self.default_func is not None:
                self[key] = self.default_func()
                return self[key]
            else:
                return None

        if self.strict and time.time() > self.times.get(key, 0):
            self.misses += 1
            self._expired_keys += 1
            del self[key]
            if self.default_func is not None:
                self[key] = self.default_func()
                return self[key]
            else:
                return None

            # raise KeyError("The key expired and strict mode is set")
        self.hits += 1
        return self.store[key]

    def __contains__(self, item):
        return item in self.times and (not self.strict or time.time() <= self.times[item])

    def __setitem__(self, key: typing.Hashable, value):
        self.store[key] = value
        self.times[key] = time.time() + self.expire_after

    def __delitem__(self, key: typing.Hashable):
        try:
            del self.store[key]
        except KeyError:
            pass

        try:
            del self.times[key]
        except KeyError:
            pass

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __str__(self):
        return f"<Cache ttl={self.expire_after} keys_stored_count={len(self.store)} strict={self.strict}>"


class Cache:
    def __init__(self, bot):
        self.bot = bot
        self.storage: Dict[str, CacheStorageDict] = {}

    def create_or_reset_cache(self, name: str, *args, **kwargs):
        self.storage[name] = CacheStorageDict(*args, **kwargs)

    def ensure_cache(self, name: str, *args, **kwargs):
        if name not in self.storage:
            self.create_or_reset_cache(name, *args, **kwargs)

    def get_cache(self, name: str, *args, **kwargs):
        self.ensure_cache(name, *args, **kwargs)
        return self.storage[name]
