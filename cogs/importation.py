from discord.ext import commands

from cogs.helpers import checks
from cogs.helpers.helpful_classes import LikeUser


class Importation:

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(4)
    @checks.bot_have_permissions()
    async def import_bans(self, ctx):
        """
        Import bans from the server banlist. If possible and available, also include the reason from the audit logs.

        This is only available to servers administrators, and can only be done once per guild.
        :param ctx:
        :return:
        """

        if await self.bot.settings.get(ctx.guild, 'imported_bans'):
            await ctx.send("You already imported your guild bans. "
                           "If you think this is an error, join the support server and ask!")
            return
        else:
            await self.bot.settings.set(ctx.guild, 'imported_bans', True)

        await ctx.send(f"Doing that, it may take a long time, please wait!")

        bans = await ctx.guild.bans()


        i = 0
        t = len(bans)
        for ban in bans:

            user = ban.user
            reason = ban.reason

            if not reason:
                reason = "No reason was provided in the audit logs"

            await self.api.add_action(ctx.guild, user, 'ban', reason,
                                      responsible_moderator=LikeUser(did=0, name="BanList Import", guild=ctx.guild))
            i += 1

        await ctx.send(f"{i}/{t} bans imported from the server ban list.")



def setup(bot):
    bot.add_cog(Importation(bot))
