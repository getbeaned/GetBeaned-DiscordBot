import datetime
import time
import typing


from cogs.helpers.time import human_timedelta
import discord
from discord.ext import commands

from cogs.helpers import checks
from cogs.helpers.converters import ForcedMember

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from cogs.helpers.context import CustomContext


async def inspect_member(ctx: 'CustomContext', inspected: typing.Union[discord.Member, discord.User]):
    e = discord.Embed(title="GetBeaned inspection")
    e.add_field(name="Name", value=inspected.name, inline=True)
    e.add_field(name="Discriminator", value=inspected.discriminator, inline=True)
    e.add_field(name="ID", value=str(inspected.id), inline=True)

    if isinstance(inspected, discord.Member):
        e.add_field(name="(Desktop) Status", value=inspected.desktop_status.name, inline=True)
        e.add_field(name="(Mobile) Status", value=inspected.mobile_status.name, inline=True)
        e.add_field(name="Status", value=inspected.status.name, inline=True)

        human_delta = human_timedelta(inspected.joined_at, source=datetime.datetime.utcnow())
        e.add_field(name="Joined at", value=str(inspected.joined_at) + f" ({human_delta})", inline=False)

    human_delta = human_timedelta(inspected.created_at, source=datetime.datetime.utcnow())
    e.add_field(name="Account created at", value=str(inspected.created_at) + f" ({human_delta})", inline=False)

    e.add_field(name="Avatar URL", value=inspected.avatar_url, inline=False)

    e.add_field(name="Default Avatar URL", value=inspected.default_avatar_url, inline=False)
    e.set_author(name=inspected.name, url=f"https://getbeaned.me/users/{inspected.id}", icon_url=inspected.avatar_url)

    await ctx.send(embed=e)


class Inspector(commands.Cog):

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.api = bot.api

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(2)
    async def inspect(self, ctx: 'CustomContext', inspected: typing.Union[discord.Member, discord.User, discord.TextChannel, discord.VoiceChannel, discord.Role]):
        """Inspect an object and return properties about it..."""
        if isinstance(inspected, discord.Member) or isinstance(inspected, discord.User):
            return await inspect_member(ctx, inspected)





def setup(bot: 'GetBeaned'):
    bot.add_cog(Inspector(bot))
