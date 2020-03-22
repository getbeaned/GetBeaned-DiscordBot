import logging
import typing

import discord
from discord.ext import commands

from cogs.helpers.hastebins import upload_text

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned  # Good hack 👌


class CustomContext(commands.Context):
    bot: 'GetBeaned'

    def __init__(self, **attrs):
        super().__init__(**attrs)

    @property
    def logger(self):
        # Copy that to log
        if self.channel:
            cname = self.channel.name
        else:
            cname = "PRIVATE_MESSAGE"

        extra = {"channelname": f"#{cname}", "userid": f"{self.author.id}", "username": f"{self.author.name}#{self.author.discriminator}"}
        logger = logging.LoggerAdapter(self.bot.base_logger, extra)
        return logger

    async def send_to(self, message: str, user: typing.Optional[discord.User] = None, **kwargs):
        if user is None:
            user = self.author

        if len(message) > 1900 and kwargs.get("embed", None) is None:
            message = await upload_text(message.strip("`"))

        message = f"{user.mention} > {message}"

        return await self.send(message, **kwargs)
