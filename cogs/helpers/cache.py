import collections
import time

from typing import Dict


class CacheStorageDict(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, expire_after=60, strict=False, *args, **kwargs):
        self.store = dict()
        self.times = dict()
        self.expire_after = expire_after
        self.strict = strict
        self.update(dict(*args, **kwargs))  # use the free update to set keys
        self._expired_keys = 0

    def get(self, key, default=None):
        try:
            r = self[key]
            if r is None:
                return default
            else:
                return r
        except KeyError:
            return default

    def cleanup(self):
        i = 0
        for key, expire in list(self.times.items()):
            if time.time() > expire:
                i += 1
                del self[key]

        self._expired_keys += i
        return i

    def get_status(self):
        status_dict = {
            "expired_keys": set(),
            "stored_keys_count": 0,
            "stored_expired_keys_count": 0,
            "expired_keys_count": 0,
        }

        for key, expire in self.times.items():
            if time.time() > expire:
                status_dict["expired_keys"].add(key)

        status_dict["stored_keys_count"] = len(self.store)
        status_dict["stored_expired_keys_count"] = len(status_dict["expired_keys"])
        status_dict["expired_keys_count"] = self._expired_keys + len(status_dict["expired_keys"])

        return status_dict

    def __getitem__(self, key):
        if key not in self.store:
            return None

        if self.strict and time.time() > self.times.get(key, 0):
            self._expired_keys += 1
            del self[key]
            return None
            # raise KeyError("The key expired and strict mode is set")

        return self.store[key]

    def __contains__(self, item):
        return item in self.times and (not self.strict or time.time() <= self.times[item])

    def __setitem__(self, key, value):
        self.store[key] = value
        self.times[key] = time.time() + self.expire_after

    def __delitem__(self, key):
        del self.store[key]
        del self.times[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)


class Cache:
    def __init__(self, bot):
        self.bot = bot
        self.storage: Dict[str, CacheStorageDict] = {}

    def create_or_reset_cache(self, name, *args, **kwargs):
        self.storage[name] = CacheStorageDict(*args, **kwargs)

    def ensure_cache(self, name, *args, **kwargs):
        if name not in self.storage:
            self.create_or_reset_cache(name, *args, **kwargs)

    def get_cache(self, name, *args, **kwargs):
        self.ensure_cache(name, *args, **kwargs)
        return self.storage[name]
