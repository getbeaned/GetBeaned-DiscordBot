import typing

import discord
from discord.ext import commands

from cogs.helpers import checks
from cogs.helpers.helpful_classes import LikeUser

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from cogs.helpers.context import CustomContext


class Importation(commands.Cog):
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.api = bot.api

    # assert staff_type in ['banned', 'trusted', 'moderators', 'admins']
    @commands.command(aliases=["addadmin"])
    @commands.guild_only()
    @checks.have_required_level(4)
    async def add_admin(self, ctx: 'CustomContext', user: typing.Union[discord.Member, discord.Role]):
        """
        Add some server admins. They can moderate the server but also edit other moderator reasons on the webinterface.

        You can manage the members you gave some access to in your server settings in the webinterface. See `m+urls`
        """

        if isinstance(user, discord.Role):
            user = LikeUser(did=user.id, name=f"[ROLE] {user.name}", guild=ctx.guild, discriminator='0000',
                            do_not_update=False)

        await self.api.add_to_staff(ctx.guild, user, 'admins')
        await ctx.send_to(':ok_hand: Done. You can edit staff on the web interface.')

    @commands.command(aliases=["addmoderator"])
    @commands.guild_only()
    @checks.have_required_level(4)
    async def add_moderator(self, ctx: 'CustomContext', user: typing.Union[discord.Member, discord.Role]):
        """
        Add a moderator on this server. Moderators can do things such as banning, kicking, warning, softbanning...

        You can manage the members you gave some access to in your server settings in the webinterface. See `m+urls`
        """

        if isinstance(user, discord.Role):
            user = LikeUser(did=user.id, name=f"[ROLE] {user.name}", guild=ctx.guild, discriminator='0000',
                            do_not_update=False)

        await self.api.add_to_staff(ctx.guild, user, 'moderators')
        await ctx.send_to(':ok_hand: Done. You can edit staff on the web interface.')

    @commands.command(aliases=["addtrusted", "addtrustedmember", "add_trusted"])
    @commands.guild_only()
    @checks.have_required_level(4)
    async def add_trusted_member(self, ctx: 'CustomContext', user: typing.Union[discord.Member, discord.Role]):
        """
        Add a trusted member on this server. Trusted members can do basic moderation actions as kicking, warning or
        noting people.

        You can manage the members you gave some access to in your server settings in the webinterface. See `m+urls`
        """

        if isinstance(user, discord.Role):
            user = LikeUser(did=user.id, name=f"[ROLE] {user.name}", guild=ctx.guild, discriminator='0000',
                            do_not_update=False)

        await self.api.add_to_staff(ctx.guild, user, 'trusted')
        await ctx.send_to(':ok_hand: Done. You can edit staff on the web interface.')

    @commands.command(aliases=["add_banned", "addbanned", "addbannedmember"])
    @commands.guild_only()
    @checks.have_required_level(4)
    async def add_banned_member(self, ctx: 'CustomContext', user: typing.Union[discord.Member, discord.Role]):
        """
        Ban a member from the bot on this server. They will get a malus on the automod, and won't be able to use most
        of the commands there

        You can manage the members you gave some access to in your server settings in the webinterface. See `m+urls`
        """

        await self.api.add_to_staff(ctx.guild, user, 'banned')
        await ctx.send_to(':ok_hand: Done. You can edit staff on the web interface.')

    @commands.command(aliases=["me"])
    @commands.guild_only()
    @checks.have_required_level(1)
    async def urls(self, ctx: 'CustomContext', user: discord.Member = None):
        """
        See your profile and other useful URLs
        """

        await self.api.add_guild(ctx.guild)
        await self.api.add_user(ctx.message.author)
        await self.api.add_user(user) if user else None

        user_id = user.id if user else ctx.message.author.id
        await ctx.send_to(f"**Useful urls**:\n"
                          f"- **Server webpage**: https://getbeaned.me/guilds/{ctx.guild.id} \n"
                          f"- **Your server profile**: https://getbeaned.me/users/{ctx.guild.id}/{user_id}\n"
                          f"- **Your global profile**: https://getbeaned.me/users/{user_id}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.guild):
        self.bot.logger.info(f"New server joined! {guild.id} - {guild.name} ({guild.member_count} members)")
        await self.api.add_guild(guild)


def setup(bot: 'GetBeaned'):
    bot.add_cog(Importation(bot))
