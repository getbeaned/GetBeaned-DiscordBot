"""
These are checks to see if some commands can be executed by users.
"""
import discord

from cogs.helpers.level import get_level
from discord.ext import commands


class PermissionsError(commands.CheckFailure):
    def __init__(self, required, current):
        self.required = required
        self.current = current


class NoPermissionsError(commands.CheckFailure):
    pass


def have_required_level(required: int = 0):
    async def predicate(ctx):
        # await ctx.bot.wait_until_ready()
        level = await get_level(ctx, ctx.message.author)
        cond = level >= required

        ctx.logger.debug(f"Check for level required returned {cond} (c={level}, r={required})")
        if cond:
            return True
        else:
            raise PermissionsError(required=required, current=level)

    return commands.check(predicate)


def bot_have_permissions():
    async def predicate(ctx):
        await ctx.bot.wait_until_ready()
        current_permissions = ctx.message.guild.me.permissions_in(ctx.channel)
        wanted_permissions = discord.permissions.Permissions.none()
        wanted_permissions.update(
            kick_members=True,
            ban_members=True,
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            external_emojis=True,
            change_nickname=True
        )

        cond = current_permissions >= wanted_permissions

        ctx.logger.debug(f"Check for permissions required returned {cond}")

        if cond:
            return True
        else:
            raise NoPermissionsError()

    return commands.check(predicate)
