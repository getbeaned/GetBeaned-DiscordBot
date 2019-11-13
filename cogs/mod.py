import asyncio

import discord
from discord.ext import commands
from cogs.helpers import checks
from cogs.helpers.actions import full_process, unban, note, warn, kick, softban, ban, mute, unmute
from cogs.helpers.converters import ForcedMember, BannedMember, InferiorMember
from cogs.helpers.helpful_classes import FakeMember
from cogs.helpers.level import get_level
from cogs.logging import save_attachments


class Mod(commands.Cog):
    """
    Moderation commands for the bot.

    Here you'll find, commands to ban, kick, warn and add notes to members.
    """

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api

    async def parse_arguments(self, ctx, users):
        if len(users) == 0:
            raise commands.BadArgument("No users provided")

        uids = [u.id for u in users]

        if ctx.author.id in uids:
            raise commands.BadArgument("Targeting self...")

        if self.bot.user.id in uids:
            raise commands.BadArgument("Targeting GetBeaned...")

        if len(users) >= 2:

            list_names = ", ".join([user.name for user in users])
            await ctx.send_to(f"⚠️ You are gonna act on multiple people at once, are you sure you want to do that ?\n"
                              f"**List of users:** {list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 15 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=15.0)
            except asyncio.TimeoutError:
                await ctx.send_to("❌ Not doing anything")
                raise commands.BadArgument("Canceled execution")

        attachments_saved_urls, attachments_unsaved_urls = await save_attachments(self.bot, ctx.message)

        if len(attachments_saved_urls) > 0:
            attachments_saved_url = attachments_saved_urls[0]
        elif len(attachments_unsaved_urls) > 0:
            attachments_saved_url = attachments_unsaved_urls[0]
        else:
            attachments_saved_url = None

        return attachments_saved_url

    async def check_reason(self, ctx, reason, attachments_saved_url):
        level = await get_level(ctx, ctx.message.author)

        justification_level_setting = await ctx.bot.settings.get(ctx.guild, "force_justification_level")

        inferior_levels = {"1": 0, "2": 3, "3": 6}

        if level < inferior_levels[justification_level_setting]:
            if attachments_saved_url is None:
                raise commands.BadArgument("You must justify your actions by attaching a screenshot to your command")
            if len(reason) < 10:
                raise commands.BadArgument("You must justify your actions by adding a detailed reason to your command")


    async def run_actions(self, ctx, users, reason, attachments_saved_url, action):
        cases_urls = []

        for user in users:
            act = await full_process(ctx.bot, action, user, ctx.author, reason, attachement_url=attachments_saved_url)
            cases_urls.append(act['url'])

        await ctx.send(f":ok_hand: - See {', '.join(cases_urls)} for details")


    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def unban(self, ctx, banned_users: commands.Greedy[BannedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = ""):
        """
        Unban a member from the server. The member must be currently banned for this command to work.

        Use like +unban [member(s)] <reason>.

        [member] can be an ID or a username.
        <reason> is your unban reason.
        """

        attachments_saved_url = await self.parse_arguments(ctx, users=[b.u for b in banned_users])
        cases_urls = []

        for ban in banned_users:
            # ban is in fact a guild.BanEntry recorvered from the ban list.
            on = ban.user
            ban_reason = ban.reason

            if ban_reason:
                reason += "\nThis user was previously banned with the following reason: " + str(ban_reason)

            if len(reason) == 0:
                reason = None

            on_member = FakeMember(guild=ctx.guild, user=on)

            act = await full_process(ctx.bot, unban, on_member, ctx.author, reason, attachement_url=attachments_saved_url)
            cases_urls.append(act['url'])

        await ctx.send(f":ok_hand: - See {', '.join(cases_urls)} for details")



    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def unmute(self, ctx, users: commands.Greedy[ForcedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = ""):
        """
        UnMute a member on the server. A mute is when you prevent a user from talking/speaking in any channel.
        Using this command require a specific role, that you can create using the +create_muted_role command

        If thresholds are enabled, muting a user can lead to kicks.

        Use like +unmute [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your mute reason.
        """
        ROLE_NAME = "GetBeaned_muted"
        muted_role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)

        if muted_role is None:
            await ctx.send_to(f"❌ The muted role does NOT exist yet. Please create it using the {ctx.prefix}create_muted_role.")
            return False

        attachments_saved_url = await self.parse_arguments(ctx, users=users)

        await self.run_actions(ctx, users, reason, attachments_saved_url, unmute)

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(2)
    async def note(self, ctx, users: commands.Greedy[ForcedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False)):
        """
        Note a member on the server. A note does nothing but store information of a specific user.

        Use like +note [member(s)] [reason].

        [member] can be an ID, a username#discrim or a mention.
        [reason] is your note reason.
        """
        # Nothing to do here.

        attachments_saved_url = await self.parse_arguments(ctx, users=users)

        await self.run_actions(ctx, users, reason, attachments_saved_url, note)

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(2)
    async def warn(self, ctx, users: commands.Greedy[ForcedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = ""):
        """
        Warn a member on the server. If thresholds are enabled, warning a user can lead to worse actions, like bans and kicks.

        Use like +warn [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your warn reason.
        """

        attachments_saved_url = await self.parse_arguments(ctx, users=users)
        await self.check_reason(ctx, reason, attachments_saved_url)

        await self.run_actions(ctx, users, reason, attachments_saved_url, warn)

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def mute(self, ctx, users: commands.Greedy[InferiorMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = ""):
        """
        Mute a member on the server. A mute is when you prevent a user from talking/speaking in any channel.
        Using this command require a specific role, that you can create using the +create_muted_role command

        If thresholds are enabled, muting a user can lead to kicks.

        Use like +mute [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your mute reason.
        """
        ROLE_NAME = "GetBeaned_muted"
        muted_role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)

        if muted_role is None:
            await ctx.send_to(f"❌ The muted role does NOT exist yet. Please create it using the {ctx.prefix}create_muted_role.")
            return False

        attachments_saved_url = await self.parse_arguments(ctx, users=users)
        await self.check_reason(ctx, reason, attachments_saved_url)

        await self.run_actions(ctx, users, reason, attachments_saved_url, mute)


    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def kick(self, ctx, users: commands.Greedy[InferiorMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = ""):
        """
        Kick a member from the server. If thresholds are enabled, kicking a user can lead to bans.

        Use like +kick [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your kick reason.
        """

        attachments_saved_url = await self.parse_arguments(ctx, users=users)
        await self.check_reason(ctx, reason, attachments_saved_url)

        await self.run_actions(ctx, users, reason, attachments_saved_url, kick)

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def softban(self, ctx, users: commands.Greedy[ForcedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = ""):
        """
        Softban a member on the server. A softban is when you ban a user to remove every message sent by him,
        before unbanning him/her so that he/she can join again.

        If thresholds are enabled, softbanning a user can lead to bans.

        Use like +softban [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your softban reason.
        """

        attachments_saved_url = await self.parse_arguments(ctx, users=users)
        await self.check_reason(ctx, reason, attachments_saved_url)

        await self.run_actions(ctx, users, reason, attachments_saved_url, softban)

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def ban(self, ctx, users: commands.Greedy[ForcedMember(may_be_banned=False)], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = ""):
        """
        Banning a user is the ultimate punishment, where is is kicked from the server and can't return

        Use like +ban [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your ban reason.
        """

        attachments_saved_url = await self.parse_arguments(ctx, users=users)
        await self.check_reason(ctx, reason, attachments_saved_url)

        await self.run_actions(ctx, users, reason, attachments_saved_url, ban)


def setup(bot):
    bot.add_cog(Mod(bot))
