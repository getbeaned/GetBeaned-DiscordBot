import typing

from discord.ext import commands

from cogs.helpers import checks

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from cogs.helpers.context import CustomContext

class Donators(commands.Cog):
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(1)
    async def make_vip(self, ctx: 'CustomContext', guild_id: int):
        """
        Makes a server a VIP server.
        """
        if not ctx.channel.id == 628878178168995853:
            await ctx.send("❌ Please run this command in the #vips channel on the GetBeaned Support Server")
            return

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            await ctx.send(f"❌ Uh uh, could not find the guild with ID {guild_id} :( Try again and make sure the bot is already in that guild.")
            return

        if ctx.author.id not in [guild.owner.id, 138751484517941259]:
            await ctx.send(f"❌ Uh uh, you are *not* the owner of the server {guild.name}.")
            return

        await self.bot.settings.set(guild, 'vip', True)
        await ctx.send(f"👌 Thanks {ctx.message.author.mention}, the server {guild.name} (ID: `{guild.id}`) is now VIP, and can use VIP settings.")


def setup(bot: 'GetBeaned'):
    bot.add_cog(Donators(bot))
