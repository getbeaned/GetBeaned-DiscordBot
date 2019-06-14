import collections
import time

from discord.ext import tasks, commands
from typing import Dict

from cogs.helpers import checks


class Cache(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.housekeeping.start()

    @commands.command()
    @checks.have_required_level(8)
    async def cache_status(self, ctx):
        status_message = []
        global_stored_keys_count = 0
        global_stored_expired_keys_count = 0
        global_expired_keys_count = 0

        for cache_dict_name, cache_dict in self.bot.cache.storage.items():
            status = cache_dict.get_status()
            # status_dict = {
            #     "expired_keys": set(),
            #     "stored_keys_count": 0,
            #     "stored_expired_keys_count": 0,
            #     "expired_keys_count": 0,
            # }
            global_stored_keys_count += status['stored_keys_count']
            global_stored_expired_keys_count += status['stored_expired_keys_count']
            global_expired_keys_count += status['expired_keys_count']

            status_message.append(f"== {cache_dict_name} ==")
            status_message.append("```diff")
            status_message.append(f"+ Currently stored keys : {status['stored_keys_count']}")
            status_message.append(f"- Currently stored expired keys : {status['stored_expired_keys_count']}")
            status_message.append(f"Total expired keys : {status['expired_keys_count']}")
            status_message.append("```")
            status_message.append("")

        percent_stored_and_expired = 0 if global_stored_keys_count == 0 else round((global_stored_expired_keys_count / global_stored_keys_count) * 100, 2)

        status_message.append(f"Totals: {global_stored_keys_count} stored,\n"
                              f"{global_stored_expired_keys_count} stored and expired ({percent_stored_and_expired} %)\n"
                              f"{global_expired_keys_count} expired")

        await ctx.send("\n".join(status_message))

    @commands.command()
    @checks.have_required_level(8)
    async def cache_cleanup(self, ctx):
        message = []
        total_deleted = 0

        for cache_dict_name, cache_dict in self.bot.cache.storage.items():
            deleted = cache_dict.cleanup()
            total_deleted += deleted
            message.append(f"{cache_dict_name}: deleted **{deleted}** expired entries")

        message.append(f"\nDeleted **{total_deleted}** entries total.")

        await ctx.send("\n".join(message))

    def cog_unload(self):
        self.housekeeping.stop()

    @tasks.loop(hours=1)
    async def housekeeping(self):
        self.bot.logger.info("Cleaning up cache")
        message = []
        total_deleted = 0

        for cache_dict_name, cache_dict in self.bot.cache.storage.items():
            deleted = cache_dict.cleanup()
            total_deleted += deleted
            message.append(f"{cache_dict_name}: deleted **{deleted}** expired entries")

        message.append(f"\nDeleted **{total_deleted}** entries total.")

        self.bot.logger.info("\n".join(message))

    @housekeeping.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()


def setup(bot):
    cache = Cache(bot)
    bot.add_cog(cache)
