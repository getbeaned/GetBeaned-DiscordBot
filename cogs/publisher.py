import collections
import io
import typing

import discord

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from discord.ext import commands


class Publisher(commands.Cog):
    """
    Used to automatically publish messages in announcement channels
    """

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if not message.guild:
            return
        if not message.channel.topic or not "[getbeaned:auto_publish]" in message.channel.topic:
            return
        if not message.channel.type == discord.ChannelType.news:
            return
        if not message.channel.permissions_for(message.guild.me).manage_messages:
            await message.channel.send("Can't publish, no perms")
            return
        await message.publish()


def setup(bot: 'GetBeaned'):
    bot.add_cog(Publisher(bot))
