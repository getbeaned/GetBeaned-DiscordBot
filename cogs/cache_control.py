import typing

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from discord.ext import tasks, commands

from cogs.helpers import checks
from cogs.helpers.context import CustomContext


class Cache(commands.Cog):
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.housekeeping.start()

    @commands.command()
    @checks.have_required_level(8)
    async def cache_status(self, ctx: 'CustomContext'):
        status_message = []
        global_stored_keys_count = 0
        global_stored_expired_keys_count = 0
        global_expired_keys_count = 0
        global_hits = 0
        global_misses = 0

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
            global_hits += status['hits']
            global_misses += status['misses']

            pct_misses = round(status['misses']/(status['hits'] + status['misses']) * 100) if status['hits'] > 0 else "XX"

            status_message.append(f"== {cache_dict_name} ==")
            status_message.append(f"`{str(cache_dict)}`")
            status_message.append("")
            status_message.append("```diff")
            status_message.append(f"+ {status['hits']} requests hit, {status['misses']} requests missed ({pct_misses}%)")
            status_message.append(f"+ Currently stored keys : {status['stored_keys_count']}")
            status_message.append(f"- Currently stored expired keys : {status['stored_expired_keys_count']}")
            status_message.append(f"Total expired keys : {status['expired_keys_count']}")
            status_message.append("```")
            status_message.append("")

            # Big enough messages
            if sum(map(len, status_message)) > 1000:
                await ctx.send("\n".join(status_message) + "")
                status_message = ["​"] # there is a ZWSP here to mark a line break

        percent_stored_and_expired = 0 if global_stored_keys_count == 0 else round((global_stored_expired_keys_count / global_stored_keys_count) * 100, 2)

        status_message.append(f"Totals: {global_stored_keys_count} stored,\n"
                              f"{global_stored_expired_keys_count} stored and expired ({percent_stored_and_expired} %)\n"
                              f"{global_expired_keys_count} expired\n{global_hits} hits and {global_misses} misses.")

        stored_messages = len(self.bot._connection._messages)
        max_messages = self.bot._connection.max_messages
        pct_max_messages = round(stored_messages/max_messages * 100, 2)

        status_message.append(f"There is {stored_messages}/{max_messages} messages stored in the bot cache ({pct_max_messages} %)")

        await ctx.send("\n".join(status_message))

    @commands.command()
    @checks.have_required_level(8)
    async def cache_cleanup(self, ctx: 'CustomContext'):
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


def setup(bot: 'GetBeaned'):
    cache = Cache(bot)
    bot.add_cog(cache)
