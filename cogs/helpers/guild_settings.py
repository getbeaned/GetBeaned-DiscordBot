import random
import time
from collections import defaultdict


class Settings:
    def __init__(self, bot):
        self.bot = bot
        self.settings_cache = bot.cache.get_cache("settings", expire_after=60, strict=True)

    async def add_to_cache(self, guild, settings):
        self.settings_cache[guild] = settings

    async def get(self, guild, setting):
        await self.bot.wait_until_ready()

        gs = self.settings_cache[guild]

        if gs:  # Use cache
            return gs[setting]
        else:
            # Get from internet
            gs = await self.bot.api.get_settings(guild)
            await self.add_to_cache(guild, gs)
            return gs[setting]

    async def set(self, guild, setting, value):
        await self.bot.wait_until_ready()

        del self.settings_cache[guild]

        await self.bot.api.set_settings(guild, setting, value)
