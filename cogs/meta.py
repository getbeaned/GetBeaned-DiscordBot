import time
import typing

import discord
from discord.ext import commands

from cogs.helpers import checks
from cogs.helpers.converters import ForcedMember

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from cogs.helpers.context import CustomContext


class Meta(commands.Cog):

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.api = bot.api

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(1)
    async def ping(self, ctx: 'CustomContext'):
        """Calculates the ping time."""

        t_1 = time.perf_counter()
        await ctx.trigger_typing()  # tell Discord that the bot is "typing", which is a very simple request
        t_2 = time.perf_counter()
        time_delta = round((t_2 - t_1) * 1000)  # calculate the time needed to trigger typing
        await ctx.send("Pong. — Time taken: {}ms".format(time_delta))  # send a message telling the user the calculated ping time

    def cleanup_code(self, content: str):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @staticmethod
    def get_syntax_error(e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(hidden=True)
    @checks.have_required_level(8)
    async def refresh_user(self, ctx: 'CustomContext', whos: commands.Greedy[ForcedMember]):
        """Refresh a user profile on the website."""

        for who in whos:
            await self.bot.api.add_user(who)
            await ctx.send_to(f"{who.name}: https://getbeaned.me/users/{who.id}")

    @commands.command()
    @checks.have_required_level(1)
    async def channel_id(self, ctx: 'CustomContext'):
        """Show the current channel ID."""
        await ctx.send_to(f"{ctx.channel.mention} ID is {ctx.channel.id}")

    @commands.command()
    @checks.have_required_level(4)
    async def fake_message(self, ctx: 'CustomContext', who: ForcedMember, *, message: str):
        """Refresh a user profile on the website."""
        avatar = await who.avatar_url.read()

        try:
            webhook = await ctx.channel.create_webhook(name=who.display_name, avatar=avatar, reason=f"Fakemessage from {ctx.message.author.name}")
        except discord.Forbidden:
            await ctx.send_to("No permission to create webhooks :(")
            return

        await webhook.send(discord.utils.escape_mentions(message))
        await webhook.delete()


def setup(bot: 'GetBeaned'):
    bot.add_cog(Meta(bot))
