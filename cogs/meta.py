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
    async def level(self, ctx, user: discord.Member = None):
        """
        Show your current access level

        -------------------------------------
        | Level | Description               |
        |-----------------------------------|
        | 10    | Bot owner (Eyesofcreeper) |
        | 09    | Reserved for future use   |
        | 08    | Bot moderators            |
        | 07    | Reserved for future use   |
        | 06    | Reserved for future use   |
        | 05    | Current server owner      |
        | 04    | Server administrator      |
        | 03    | Server moderator          |
        | 02    | Trusted users             |
        | 01    | Normal members            |
        | 00    | Users banned from the bot |
        -------------------------------------
        """

        if user is None:
            user = ctx.message.author

        l = await get_level(ctx, user)

        levels_names = {10: "Bot owner",
                        9: "Reserved for future use",
                        8: "Bot global-moderators",
                        7: "Reserved for future use",
                        6: "Reserved for future use",
                        5: "Server owner",
                        4: "Server administrator",
                        3: "Server moderator",
                        2: "Server trusted user",
                        1: "Member",
                        0: "Bot-banned"
                        }

        await ctx.send(f"Current level: {l} ({levels_names[l]})")

    @commands.command(aliases=["permissions_check", "permission_check"])
    @commands.guild_only()
    @checks.have_required_level(1)
    async def bot_permissions_check(self, ctx):
        current_permissions:discord.Permissions = ctx.message.guild.me.permissions_in(ctx.channel)

        emojis = {
            True: "✅",
            False: "❌"
        }

        perms_check = []

        for permission in ["kick_members", "ban_members", "read_messages", "send_messages", "manage_messages", "embed_links", "attach_files",
            "read_message_history", "external_emojis", "change_nickname", "view_audit_log"]:
            have_perm = current_permissions.__getattribute__(permission)
            emoji = emojis[have_perm]
            perms_check.append(
                f"{emoji}\t{permission}"
            )

        await ctx.send("\n".join(perms_check))

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
            await ctx.send_to(f"{who.name}: https://getbeaned.api-d.com/users/{who.id}")

    @commands.command()
    @checks.have_required_level(1)
    async def channel_id(self, ctx):
        """Show the current channel ID."""
        await ctx.send_to(f"{ctx.channel.mention} ID is {ctx.channel.id}")

def setup(bot):
    bot.add_cog(Meta(bot))
