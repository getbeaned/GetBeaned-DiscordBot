import typing

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

import discord
from discord.ext import commands

from cogs.helpers import checks
from cogs.helpers.helpful_classes import LikeUser
from cogs.helpers.level import get_level
from cogs.helpers.actions import full_process, note, warn
from cogs.helpers.context import CustomContext

import string


class FakeCtx:
    def __init__(self, guild: discord.Guild, bot: 'GetBeaned'):
        self.guild = guild
        self.bot = bot


class Dehoister(commands.Cog):
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.bypass = bot.cache.get_cache("dehoister_bypass", expire_after=3, strict=True, default=list)

    async def dehoist_user_in_guild(self, user: typing.Union[discord.User, discord.Member], guild: discord.Guild) -> bool:
        if await self.bot.settings.get(guild, "dehoist_enable"):
            member = guild.get_member(user.id)
            if user.id in self.bypass[guild]:
                return False

            if await get_level(FakeCtx(guild, self.bot), member) >= int(await self.bot.settings.get(guild, "dehoist_ignore_level")):
                return False

            intensity = int(await self.bot.settings.get(guild, "dehoist_intensity"))

            previous_nickname = member.display_name
            new_nickname = previous_nickname

            if intensity >= 1:
                for pos, char in enumerate(new_nickname):
                    if char in ["!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/"]:
                        new_nickname = new_nickname[1:]
                        continue
                    else:
                        break

            if intensity >= 2:
                for pos, char in enumerate(new_nickname):
                    if char not in string.ascii_letters:
                        new_nickname = new_nickname[1:]
                        continue
                    else:
                        break

            if intensity >= 3:
                new_nickname += "zz"

                while new_nickname.lower()[:2] == "aa":
                    new_nickname = new_nickname[2:]

                new_nickname = new_nickname[:-2]

            if previous_nickname != new_nickname:
                if len(new_nickname) == 0:
                    new_nickname = "z_Nickname_DeHoisted"

                self.bot.logger.info(f"Dehoisted user {previous_nickname} -> {new_nickname} in {guild}")

                reason = f"Automatic nickname DeHoist from {previous_nickname} to {new_nickname}. " \
                         f"Please try not to use special chars at the start of your nickname to appear at the top of the list of members."

                await member.edit(nick=new_nickname, reason=reason)

                actions_to_take = {
                    "note": note,
                    "warn": warn,
                    "message": None,
                    "nothing": None
                }
                action_name = await self.bot.settings.get(guild, "dehoist_action")

                action_coroutine = actions_to_take[action_name]

                if action_coroutine:
                    moderator = LikeUser(did=3, name="DeHoister", guild=guild)
                    await full_process(self.bot, action_coroutine, member, moderator, reason)

                if action_name != "nothing":

                    try:
                        await member.send(f"Your nickname/username was dehoisted on {guild.name}. "
                                          f"Please try not to use special chars at the start of your nickname to appear at the top of the list of members. "
                                          f"Thanks! Your new nickname is now `{new_nickname}`")
                    except discord.Forbidden:
                        pass

                return True
            else:
                return False
        else:
            return False

    async def dehoist_user(self, user: discord.User):
        for guild in self.bot.guilds:
            if user in guild.members:
                await self.dehoist_user_in_guild(user, guild)

    @commands.command(aliases=["rename_user", "rename_member"])
    @commands.guild_only()
    @checks.have_required_level(2)
    @checks.bot_have_permissions()
    @commands.cooldown(rate=10, per=30, type=commands.BucketType.guild)
    async def rename(self, ctx: 'CustomContext', user: discord.Member, *, name: str = None):

        await ctx.send(f"Processing, please wait.")

        self.bypass[ctx.guild].append(user.id)
        self.bypass.reset_expiry(ctx.guild)
        await user.edit(nick=name)
        await ctx.send(f"User renamed!")

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(4)
    @checks.bot_have_permissions()
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.guild)
    async def dehoist_users(self, ctx: 'CustomContext'):
        guild = ctx.guild
        dehoisted_users_count = 0

        await ctx.send(f"Processing, please wait.")

        for member in guild.members:
            dehoisted_users_count += int(await self.dehoist_user_in_guild(member, guild))

        await ctx.send(f"{dehoisted_users_count} users were dehoisted.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick != after.nick:
            self.bot.logger.debug(f"A member in {after.guild} changed nick ({before.nick} -> {after.nick}), running dehoister")

            await self.dehoist_user_in_guild(after, after.guild)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        if before.name != after.name:
            self.bot.logger.debug(f"A user changed name ({before.name} -> {after.name}), running dehoister")

            await self.dehoist_user(after)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self.bot.logger.debug(f"User {member} joined {member.guild}, running dehoister")
        await self.dehoist_user_in_guild(member, member.guild)


def setup(bot: 'GetBeaned'):
    bot.add_cog(Dehoister(bot))
