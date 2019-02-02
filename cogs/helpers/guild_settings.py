import random
import time
from collections import defaultdict


class Settings:
    def __init__(self, bot):
        self.bot = bot
        self.settings_cache = {}
        self.stats = {'internet_requests': 0,
                      'cache_requests': 0,
                      'cache_invalidations': 0,
                      'pre_cache_invalidations': 0
                      }

    async def get_not_expired(self, guild):
        gs = self.settings_cache.get(guild, None)
        if not gs:
            return None
        else:
            gse = gs["expire"]
            if gse < time.time():
                self.stats['cache_invalidations'] += 1
                return None
            else:
                return gs["content"]

    async def add_to_cache(self, guild, settings):
        self.settings_cache[guild] = {"expire": int(time.time()) + 60, "content": settings}

    async def cleanup_cache(self):
        for guild in self.settings_cache.copy().keys():
            if self.settings_cache[guild]["expire"] <= time.time():
                del self.settings_cache[guild]
                self.stats['pre_cache_invalidations'] += 1

    async def get(self, guild, setting):
        await self.bot.wait_until_ready()

        gs = await self.get_not_expired(guild)

        if gs:  # Use cache
            self.stats['cache_requests'] += 1
            return gs[setting]
        else:
            # Get from internet
            self.stats['internet_requests'] += 1
            gs = await self.bot.api.get_settings(guild)
            await self.add_to_cache(guild, gs)

            if random.randint(0,1000) == 0:  # 0.1% chance of cleaning cache
                self.bot.logger.debug("Cleaning cache")
                await self.cleanup_cache()
            return gs[setting]

    async def set(self, guild, setting, value):
        await self.bot.wait_until_ready()

        del self.settings_cache[guild]

        await self.bot.api.set_settings(guild, setting, value)


