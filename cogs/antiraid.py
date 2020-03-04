import collections
import datetime

import discord
import typing

from discord.ext import commands

from cogs.helpers.actions import full_process, softban, ban
from cogs.helpers.helpful_classes import LikeUser

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned


class AntiRaid(commands.Cog):
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.join_history = self.bot.cache.get_cache("antiraid_recently_joined", expire_after=600, default=lambda: collections.deque(maxlen=14))
        self.acted_on = self.bot.cache.get_cache("antiraid_acted_on", expire_after=1200, default=list)

    async def check_same_avatar(self, members, min_number_of_same_avatar: int = 3, ignore_no_avatar: bool = True) -> typing.List[discord.Member]:
        counts = collections.defaultdict(lambda: [0, []])
        for member in members:
            member: discord.Member
            if member.avatar is not None and ignore_no_avatar:
                counts[member.avatar][0] += 1
                counts[member.avatar][1].append(member)

        flagged = []
        for count in counts.values():
            if count[0] >= min_number_of_same_avatar:
                flagged.extend(count[1])

        return flagged

    async def sanity_check(self, members: typing.List[discord.Member]) -> typing.List[discord.Member]:
        bad_members = []
        for member in members:
            if not member.is_avatar_animated() and datetime.datetime.now() - datetime.timedelta(days=3) < member.created_at:
                bad_members.append(member)
        return bad_members

    async def add_to_history(self, member: discord.Member):
        if member not in self.join_history[member.guild]:
            self.join_history[member.guild].append(member)
            self.join_history.reset_expiry(member.guild)
            self.acted_on.reset_expiry(member.guild)
            return True
        else:
            return False  # Already checked this guy.

    async def get_history(self, guild: discord.Guild):
        return self.join_history[guild]

    async def remove_already_acted_on(self, guild: discord.Guild, members: typing.Iterable[discord.Member]) -> typing.List[discord.Member]:
        return list(set(members) - set(self.acted_on[guild]))

    async def run_actions(self, guild: discord.Guild, bad_members: typing.List[discord.Member]):
        if len(bad_members) == 0:
            return 'No members to act on.'

        logging_channel = await self.bot.get_cog('Logging').get_logging_channel(guild, "logs_autoinspect_channel_id")

        if not logging_channel:
            return 'No logging channel configured for AutoInspect/AntiRaid.'

        action = await self.bot.settings.get(guild, "autoinspect_antiraid")

        if action == 1:
            return 'Nothing to do.'

        autoinspect_user = LikeUser(did=4, name="AutoInspector", guild=guild)
        # await full_process(self.bot, note, context["member"], autoinspect_user, reason=f"Automatic note by AutoInspect {name}, following a positive check.")

        embed = discord.Embed()

        embed.colour = discord.colour.Color.red()

        embed.title = f"AutoInspect AntiRaid | Positive Result"
        embed.description = f"AutoInspect AntiRaid triggered!"

        embed.set_author(name=self.bot.user.name)
        embed.add_field(name="Member(s) ID(s)", value=str([m.id for m in bad_members]))

        await logging_channel.send(embed=embed)

        for member in bad_members:
            if action == 3:
                await full_process(self.bot, softban, member, autoinspect_user, reason=f"Automatic softban by AutoInspect AntiRaid")
                return False
            elif action == 4:
                await full_process(self.bot, ban, member, autoinspect_user, reason=f"Automatic ban by AutoInspect AntiRaid")
                return False

    async def run_guild_checks(self, guild: discord.Guild):
        if not await self.bot.settings.get(guild, 'autoinspect_enable'):
            return 'AutoInspect disabled on this guild.'

        history = await self.get_history(guild)
        bad_avatar = await self.check_same_avatar(history)
        bad_members = await self.remove_already_acted_on(guild, bad_avatar)
        bad_members = await self.sanity_check(bad_members)

        self.acted_on[guild]: list

        self.acted_on[guild].extend(bad_members)
        self.acted_on.reset_expiry(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.bot.wait_until_ready()
        await self.add_to_history(member)
        await self.run_guild_checks(member.guild)


def setup(bot: 'GetBeaned'):
    bot.add_cog(AntiRaid(bot))
