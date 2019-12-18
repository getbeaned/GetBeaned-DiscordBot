import typing

import discord
from discord.ext import commands

from cogs.helpers.context import CustomContext
from cogs.helpers.helpful_classes import LikeUser, FakeMember


class NotStrongEnough(Exception):
    pass


class HierarchyError(Exception):
    pass


## Converters
# Stolen from R.Danny source code, as should do any discord bot anyway
# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py#L63
class InferiorMember(commands.Converter):
    async def convert(self, ctx: CustomContext, argument) -> discord.Member:
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
            can_execute = ctx.author == ctx.guild.owner or \
                          ctx.author.top_role > m.top_role
        except commands.BadArgument:
            raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
        else:
            if can_execute:
                if m.top_role > ctx.guild.me.top_role:
                    raise NotStrongEnough(f'You cannot do this action on this user due to role hierarchy between the bot and {m.name}.')
                return m  # We return a Member
            else:
                raise HierarchyError('You cannot do this action on this user due to role hierarchy.')


class ForcedMember(commands.Converter):
    def __init__(self, may_be_banned=True):
        super().__init__()
        self.may_be_banned = may_be_banned

    async def convert(self, ctx: CustomContext, argument) -> typing.Union[discord.Member, FakeMember, LikeUser]:
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
            return m
        except commands.BadArgument:
            try:
                did = int(argument, base=10)
                if did < 10 * 15:  # Minimum 21154535154122752 (17 digits, but we are never too safe)
                    raise commands.BadArgument(f"The discord ID {argument} provided is too small to be a real discord user-ID. Please check your input and try again.")

                if not self.may_be_banned:
                    if discord.utils.find(lambda u: u.user.id == did, await ctx.guild.bans()):
                        raise commands.BadArgument(f"The member {argument} is already banned.")

                try:
                    u = ctx.bot.get_user(did)
                    if u:
                        return FakeMember(u, ctx.guild)

                    else:
                        u = await ctx.bot.fetch_user(did)
                        return FakeMember(u, ctx.guild)
                except:
                    ctx.logger.exception("An error happened trying to convert a discord ID to a User instance. "
                                         "Relying on a LikeUser")
                    return LikeUser(did=int(argument, base=10), name="Unknown member", guild=ctx.guild)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
        except Exception as e:
            raise


class BannedMember(commands.Converter):
    async def convert(self, ctx: CustomContext, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)

            entity = discord.utils.find(lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument("Not a valid previously-banned member.")

        return entity
