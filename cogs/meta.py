import copy
import time
from typing import Union

import discord
from discord.ext import commands

from cogs.helpers import checks, context
from cogs.helpers.converters import ForcedMember
from cogs.helpers.level import get_level

import asyncio
import traceback
import inspect
import textwrap
from contextlib import redirect_stdout
import io

# to expose to the eval command
import datetime
from collections import Counter


class Meta(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.api = bot.api

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(1)
    async def ping(self, ctx):
        """Calculates the ping time."""

        t_1 = time.perf_counter()
        await ctx.trigger_typing()  # tell Discord that the bot is "typing", which is a very simple request
        t_2 = time.perf_counter()
        time_delta = round((t_2-t_1)*1000)  # calculate the time needed to trigger typing
        await ctx.send("Pong. — Time taken: {}ms".format(time_delta))  # send a message telling the user the calculated ping time

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(hidden=True)
    @checks.have_required_level(8)
    async def refresh_user(self, ctx, whos: commands.Greedy[ForcedMember]):
        """Refresh a user profile on the website."""

        for who in whos:
            await self.bot.api.add_user(who)
            await ctx.send_to(f"{who.name}: https://getbeaned.me/users/{who.id}")

    @commands.command()
    @checks.have_required_level(1)
    async def channel_id(self, ctx):
        """Show the current channel ID."""
        await ctx.send_to(f"{ctx.channel.mention} ID is {ctx.channel.id}")

    @commands.command()
    @checks.have_required_level(5)
    async def fake_message(self, ctx, who: ForcedMember, *, message:str):
        """Refresh a user profile on the website."""
        avatar = await who.avatar_url.read()

        try:
            webhook = await ctx.channel.create_webhook(name=who.display_name, avatar=avatar, reason=f"Fakemessage from {ctx.message.author.name}")
        except discord.Forbidden:
            await ctx.send_to("No permission to create webhooks :(")
            return

        await webhook.send(message)
        await webhook.delete()

def setup(bot):
    bot.add_cog(Meta(bot))
