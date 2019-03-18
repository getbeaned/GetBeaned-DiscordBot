from discord.ext import commands

class Support(commands.Cog):
    """Cog for various support commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild is None:
            return

        if message.author is self.bot:
            return

        pm_channel = self.bot.get_channel(557294214417874945)

        await pm_channel.send(f"{message.author.mention} ({message.author.name}#{message.author.discriminator})\n```{message.content[:1900]}```")

def setup(bot):
    bot.add_cog(Support(bot))
