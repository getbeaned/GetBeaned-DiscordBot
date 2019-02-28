import discord
from discord.ext import commands

from cogs.helpers import checks


class Importation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api

    # assert staff_type in ['banned', 'trusted', 'moderators', 'admins']
    @commands.command(aliases=["addadmin"])
    @commands.guild_only()
    @checks.have_required_level(4)
    async def add_admin(self, ctx, user: discord.Member):
        """
        Add some server admins. They can moderate the server but also edit other moderator reasons on the webinterface.

        You can manage the members you gave some access to in your server settings in the webinterface. See `m+urls`
        """

        await self.api.add_to_staff(ctx.guild, user, 'admins')
        await ctx.send_to(':ok_hand: Done. You can edit staff on the web interface.')

    @commands.command(aliases=["addmoderator"])
    @commands.guild_only()
    @checks.have_required_level(4)
    async def add_moderator(self, ctx, user: discord.Member):
        """
        Add a moderator on this server. Moderators can do things such as banning, kicking, warning, softbanning...

        You can manage the members you gave some access to in your server settings in the webinterface. See `m+urls`
        """

        await self.api.add_to_staff(ctx.guild, user, 'moderators')
        await ctx.send_to(':ok_hand: Done. You can edit staff on the web interface.')

    @commands.command(aliases=["addtrusted", "addtrustedmember", "add_trusted"])
    @commands.guild_only()
    @checks.have_required_level(4)
    async def add_trusted_member(self, ctx, user: discord.Member):
        """
        Add a trusted member on this server. Trusted members can do basic moderation actions as kicking, warning or
        noting people.

        You can manage the members you gave some access to in your server settings in the webinterface. See `m+urls`
        """

        await self.api.add_to_staff(ctx.guild, user, 'trusted')
        await ctx.send_to(':ok_hand: Done. You can edit staff on the web interface.')

    @commands.command(aliases=["add_banned", "addbanned", "addbannedmember"])
    @commands.guild_only()
    @checks.have_required_level(4)
    async def add_banned_member(self, ctx, user: discord.Member):
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
    async def urls(self, ctx, user: discord.Member = None):
        """
        See your profile and other useful URLs
        """

        await self.api.add_guild(ctx.guild)
        await self.api.add_user(ctx.message.author)
        await self.api.add_user(user) if user else None

        user_id = user.id if user else ctx.message.author.id
        await ctx.send_to(f"**Useful urls**:\n"
                          f"- **Server webpage**: https://getbeaned.api-d.com/guilds/{ctx.guild.id} \n"
                          f"- **Your server profile**: https://getbeaned.api-d.com/users/{ctx.guild.id}/{user_id}\n"
                          f"- **Your global profile**: https://getbeaned.api-d.com/users/{user_id}")

    @commands.command(aliases=["info", "join"])
    @commands.guild_only()
    @checks.have_required_level(1)
    async def invite(self, ctx):
        """
        Get this bot invite link
        """
        await ctx.send_to(
            "https://discordapp.com/oauth2/authorize?client_id=492797767916191745&permissions=201714887&scope=bot")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.guild):
        self.bot.logger.info(f"New server joined! {guild.id} - {guild.name} ({guild.member_count} members)")
        await self.api.add_guild(guild)


def setup(bot):
    bot.add_cog(Importation(bot))
