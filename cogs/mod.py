import asyncio

import discord
from discord.ext import commands
from cogs.helpers import checks
from cogs.helpers.actions import full_process, unban, note, warn, kick, softban, ban, mute, unmute
from cogs.helpers.converters import ForcedMember, BannedMember, InferiorMember
from cogs.helpers.helpful_classes import FakeMember


class Mod(commands.Cog):
    """
    Moderation commands for the bot.

    Here you'll find, commands to ban, kick, warn and add notes to members.
    """

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def unban(self, ctx, banned_users: commands.Greedy[BannedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = None):
        """
        Unban a member from the server. The member must be currently banned for this command to work.

        Use like +unban [member(s)] <reason>.

        [member] can be an ID or a username.
        <reason> is your unban reason.
        """

        if len(banned_users) >= 2:
            bans_list_names = ", ".join([b.user.name for b in banned_users])
            await ctx.send_to(f":warning: You are gonna unban multiple people at once, are you sure you want to do that ?\n"
                              f"**To be unbanned:** {bans_list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 10 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.send_to("Not doing anything")
                return None

        for ban in banned_users:
            # ban is in fact a guild.BanEntry recorvered from the ban list.
            on = ban.user
            ban_reason = ban.reason

            if ban_reason:
                reason += "\nThis user was previously banned with the following reason: " + str(ban_reason)

            if len(reason) == 0:
                reason = None

            if ctx.message.attachments:
                attachments_url = ctx.message.attachments[0].url
            else:
                attachments_url = None

            on_member = FakeMember(guild=ctx.guild, user=on)

            act = await full_process(ctx.bot, unban, on_member, ctx.author, reason, attachement_url=attachments_url)
            await ctx.send(f":ok_hand: - See {act['url']} for details")

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def unmute(self, ctx, users: commands.Greedy[ForcedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = None):
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

        if len(users) >= 2:
            bans_list_names = ", ".join([b.name for b in users])
            await ctx.send_to(
                f":warning: You are gonna unmute multiple people at once, are you sure you want to do that ?\n"
                f"**To be softbanned:** {bans_list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 10 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.send_to("Not doing anything")
                return None

        for on in users:
            if on.id == ctx.author.id:
                await ctx.send_to("You wouldn't do that to yourself ?")
                continue
            elif on.id == self.bot.user.id:
                await ctx.send_to("I'm innocent, I won't allow you to do that on me")
                continue

            if ctx.message.attachments:
                attachments_url = ctx.message.attachments[0].url
            else:
                attachments_url = None

            act = await full_process(ctx.bot, unmute, on, ctx.author, reason, attachement_url=attachments_url)
            await ctx.send(f":ok_hand: - See {act['url']} for details")


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

        if len(users) >= 2:
            bans_list_names = ", ".join([b.name for b in users])
            await ctx.send_to(f":warning: You are gonna note multiple people at once, are you sure you want to do that ?\n"
                              f"**To be noted:** {bans_list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 10 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.send_to("Not doing anything")
                return None

        for on in users:
            if on.id == ctx.author.id:
                await ctx.send_to("You wouldn't do that to yourself ?")
                continue
            elif on.id == self.bot.user.id:
                await ctx.send_to("I'm innocent, I won't allow you to do that on me")
                continue

            if ctx.message.attachments:
                attachments_url = ctx.message.attachments[0].url
            else:
                attachments_url = None

            act = await full_process(ctx.bot, note, on, ctx.author, reason, attachement_url=attachments_url)
            await ctx.send(f":ok_hand: - See {act['url']} for details")

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(2)
    async def warn(self, ctx, users: commands.Greedy[ForcedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = None):
        """
        Warn a member on the server. If thresholds are enabled, warning a user can lead to worse actions, like bans and kicks.

        Use like +warn [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your warn reason.
        """
        if len(users) >= 2:
            bans_list_names = ", ".join([b.name for b in users])
            await ctx.send_to(
                f":warning: You are gonna warn multiple people at once, are you sure you want to do that ?\n"
                f"**To be warned:** {bans_list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 10 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.send_to("Not doing anything")
                return None

        for on in users:
            if on.id == ctx.author.id:
                await ctx.send_to("You wouldn't do that to yourself ?")
                continue
            elif on.id == self.bot.user.id:
                await ctx.send_to("I'm innocent, I won't allow you to do that on me")
                continue

            if ctx.message.attachments:
                attachments_url = ctx.message.attachments[0].url
            else:
                attachments_url = None

            act = await full_process(ctx.bot, warn, on, ctx.author, reason, attachement_url=attachments_url)
            await ctx.send(f":ok_hand: - See {act['url']} for details")

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def mute(self, ctx, users: commands.Greedy[ForcedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False)=None):
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

        if len(users) >= 2:
            bans_list_names = ", ".join([b.name for b in users])
            await ctx.send_to(
                f":warning: You are gonna mute multiple people at once, are you sure you want to do that ?\n"
                f"**To be softbanned:** {bans_list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 10 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.send_to("Not doing anything")
                return None

        for on in users:
            if on.id == ctx.author.id:
                await ctx.send_to("You wouldn't do that to yourself ?")
                continue
            elif on.id == self.bot.user.id:
                await ctx.send_to("I'm innocent, I won't allow you to do that on me")
                continue

            if ctx.message.attachments:
                attachments_url = ctx.message.attachments[0].url
            else:
                attachments_url = None

            act = await full_process(ctx.bot, mute, on, ctx.author, reason, attachement_url=attachments_url)
            await ctx.send(f":ok_hand: - See {act['url']} for details")


    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(2)
    async def kick(self, ctx, users: commands.Greedy[InferiorMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = None):
        """
        Kick a member from the server. If thresholds are enabled, kicking a user can lead to bans.

        Use like +kick [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your kick reason.
        """
        if len(users) >= 2:
            bans_list_names = ", ".join([b.name for b in users])
            await ctx.send_to(
                f":warning: You are gonna kick multiple people at once, are you sure you want to do that ?\n"
                f"**To be kicked:** {bans_list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 10 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.send_to("Not doing anything")
                return None

        for on in users:
            if on.id == ctx.author.id:
                await ctx.send_to("You wouldn't do that to yourself ?")
                continue
            elif on.id == self.bot.user.id:
                await ctx.send_to("I'm innocent, I won't allow you to do that on me")
                continue

            if ctx.message.attachments:
                attachments_url = ctx.message.attachments[0].url
            else:
                attachments_url = None

            act = await full_process(ctx.bot, kick, on, ctx.author, reason, attachement_url=attachments_url)
            await ctx.send(f":ok_hand: - See {act['url']} for details")

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def softban(self, ctx, users: commands.Greedy[ForcedMember], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = None):
        """
        Softban a member on the server. A softban is when you ban a user to remove every message sent by him,
        before unbanning him/her so that he/she can join again.

        If thresholds are enabled, softbanning a user can lead to bans.

        Use like +softban [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your softban reason.
        """
        if len(users) >= 2:
            bans_list_names = ", ".join([b.name for b in users])
            await ctx.send_to(
                f":warning: You are gonna softban multiple people at once, are you sure you want to do that ?\n"
                f"**To be softbanned:** {bans_list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 10 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.send_to("Not doing anything")
                return None

        for on in users:
            if on.id == ctx.author.id:
                await ctx.send_to("You wouldn't do that to yourself ?")
                continue
            elif on.id == self.bot.user.id:
                await ctx.send_to("I'm innocent, I won't allow you to do that on me")
                continue

            if ctx.message.attachments:
                attachments_url = ctx.message.attachments[0].url
            else:
                attachments_url = None

            act = await full_process(ctx.bot, softban, on, ctx.author, reason, attachement_url=attachments_url)
            await ctx.send(f":ok_hand: - See {act['url']} for details")

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_permissions()
    @checks.have_required_level(3)
    async def ban(self, ctx, users: commands.Greedy[ForcedMember(may_be_banned=False)], *, reason: commands.clean_content(fix_channel_mentions=True, use_nicknames=False) = None):
        """
        Banning a user is the ultimate punishment, where is is kicked from the server and can't return

        Use like +ban [member(s)] <reason>.

        [member] can be an ID, a username#discrim or a mention.
        <reason> is your ban reason.
        """
        if len(users) >= 2:
            bans_list_names = ", ".join([b.name for b in users])
            await ctx.send_to(
                f":warning: You are gonna ban multiple people at once, are you sure you want to do that ?\n"
                f"**To be banned:** {bans_list_names}")

            await ctx.send_to("To confirm, say `ok` within the next 10 seconds")

            def check(m):
                return m.content == 'ok' and m.channel == ctx.channel and m.author == ctx.author

            try:
                await self.bot.wait_for('message', check=check, timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.send_to("Not doing anything")
                return None

        for on in users:
            if on.id == ctx.author.id:
                await ctx.send_to("You wouldn't do that to yourself ?")
                continue
            elif on.id == self.bot.user.id:
                await ctx.send_to("I'm innocent, I won't allow you to do that on me")
                continue

            if ctx.message.attachments:
                attachments_url = ctx.message.attachments[0].url
            else:
                attachments_url = None

            act = await full_process(ctx.bot, ban, on, ctx.author, reason, attachement_url=attachments_url)

            await ctx.send(f":ok_hand: - See {act['url']} for details")


def setup(bot):
    bot.add_cog(Mod(bot))
