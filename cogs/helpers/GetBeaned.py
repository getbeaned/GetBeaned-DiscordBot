import collections
import datetime
import json
import logging
import traceback

import discord
import typing
from discord.ext import commands as commands

from cogs.helpers import api
from cogs.helpers import context, checks
from cogs.helpers.cache import Cache
from cogs.helpers.converters import NotStrongEnough, HierarchyError
from cogs.helpers.guild_settings import Settings


class GetBeaned(commands.AutoShardedBot):
    def __init__(self, command_prefix: typing.Union[str, typing.Callable[[discord.Message], typing.Awaitable]], base_logger: logging.Logger, logger: logging.Logger, **options):
        super().__init__(command_prefix, **options)

        self.cache = Cache(self)
        self.commands_used = collections.Counter()
        self.admins = [138751484517941259]
        self.messages_seen = 0
        self.base_logger, self.logger = base_logger, logger

        # Load credentials so they can be used later
        with open("credentials.json", "r") as f:
            credentials = json.load(f)

        self.token = credentials["discord_token"]

        self.uptime = datetime.datetime.utcnow()

        self.api = api.Api(self)

        self.settings = Settings(self)

    async def on_message(self, message):
        self.messages_seen += 1
        if message.author.bot:
            return  # ignore messages from other bots

        ctx = await self.get_context(message, cls=context.CustomContext)
        if ctx.prefix is not None:
            await self.invoke(ctx)

    async def on_command(self, ctx: context.CustomContext):
        self.commands_used[ctx.command.name] += 1
        ctx.logger.info(f"<{ctx.command}> {ctx.message.clean_content}")
        discret_mode = await self.settings.get(ctx.guild, "bot_discret")
        if discret_mode:
            await ctx.message.delete(delay=7)


    async def on_ready(self):
        game = discord.Game(name=f"g+help | g+urls")
        await self.change_presence(status=discord.Status.online, activity=game)
        self.logger.info("We are all set, on_ready was fired! Yeah!")
        total_members = len(self.users)
        self.logger.info(f"I see {len(self.guilds)} guilds, and {total_members} members")

    async def on_command_error(self, context: context.CustomContext, exception):
        if isinstance(exception, discord.ext.commands.errors.CommandNotFound):
            return

        context.logger.debug(f"Error during processing: {exception} ({repr(exception)})")

        if isinstance(exception, discord.ext.commands.errors.MissingRequiredArgument):
            await context.send_to(f":x: A required argument is missing.\nUse it like : `{context.prefix}{context.command.signature}`", delete_after=60)
            await context.message.delete(delay=60)

            return
        elif isinstance(exception, checks.NoPermissionsError):
            await context.send_to(f":x: Oof, there was a problem! "
                                  f"The bot need more permissions to work. Please see a server admin about that. "
                                  f"If you are an admin, please type {context.prefix}bot_permissions_check to see what permissions are missing. "
                                  f"Remember to check for channel overwrites")
            return
        elif isinstance(exception, checks.PermissionsError):
            await context.send_to(f":x: Heh, you don't have the required permissions to run this command! "
                                  f"You are level {exception.current}, and you'd need {exception.required} :(", delete_after=60)
            await context.message.delete(delay=60)
            return
        # elif isinstance(exception, discord.ext.commands.errors.CheckFailure):
        #       return
        elif isinstance(exception, discord.ext.commands.errors.ConversionError):
            if isinstance(exception.original, NotStrongEnough):
                await context.send_to(f":x: Even if you have the required level to run this command, you can't target "
                                      f"someone with a higher/equal level than you :("
                                      f"```{exception.original}```", delete_after=60)
                await context.message.delete(delay=60)
                return
            elif isinstance(exception.original, HierarchyError):
                await context.send_to(f":x: You have the required level to run this command, but I can't do this "
                                      f"as your target is higher in the hierarchy than me. To fix this, move my role "
                                      f"to the top of the list in this server roles list"
                                      f"```{exception.original}```")
                return
        elif isinstance(exception, discord.ext.commands.errors.BadArgument):
            await context.send_to(f":x: An argument provided is incorrect: \n"
                                  f"**{exception}**", delete_after=60)
            await context.message.delete(delay=60)
            return
        elif isinstance(exception, discord.ext.commands.errors.ArgumentParsingError):
            await context.send_to(f":x: There was a problem parsing your command, please ensure all quotes are correct: \n"
                                  f"**{exception}**", delete_after=60)
            await context.message.delete(delay=60)
            return
        elif isinstance(exception, discord.ext.commands.errors.BadUnionArgument):
            await context.send_to(f":x: There was a problem parsing your arguments, please ensure the are the correct type: \n"
                                  f"**{exception}**", delete_after=60)
            await context.message.delete(delay=60)
            return
        elif isinstance(exception, discord.ext.commands.errors.CommandOnCooldown):
            if context.message.author.id in [138751484517941259]:
                await context.reinvoke()
                return
            else:

                await context.send_to("You are on cooldown :(, try again in {seconds} seconds".format(
                    seconds=round(exception.retry_after, 1)), delete_after=60)
                return
        elif isinstance(exception, discord.ext.commands.errors.TooManyArguments):
            await context.send_to(f":x: You gave me to many arguments. You may want to use quotes.\nUse the command like : `{context.prefix}{context.command.signature}`", delete_after=60)
            await context.message.delete(delay=60)
            return
        elif isinstance(exception, discord.ext.commands.NoPrivateMessage):
            await context.send_to('This command cannot be used in private messages.')
            return
        elif isinstance(exception, discord.ext.commands.errors.CommandInvokeError):
            await context.author.send(f"Sorry, an error happened processing your command. "
                                      f"Please review the bot permissions and try again. To report a bug, please give the support staff the following: ```py\n{exception}\n{''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))}\n```", delete_after=3600)
            await context.message.delete(delay=3600)
            return
        elif isinstance(exception, discord.ext.commands.errors.NotOwner):
            return  # Jsk uses this
        elif isinstance(exception, discord.ext.commands.errors.MaxConcurrencyReached):
            await context.send_to(str(exception),
                                      delete_after=3600)
            await context.message.delete(delay=3600)
        else:
            self.logger.error('Ignoring exception in command {}:'.format(context.command))
            self.logger.error("".join(traceback.format_exception(type(exception), exception, exception.__traceback__)))


async def get_prefix(bot: GetBeaned, message: discord.Message):
    forced_prefixes = ["g+", "g!", "gb", "gb!", "gb+"]

    if not message.guild:
        return commands.when_mentioned_or(*forced_prefixes)(bot, message)

    prefix_set = await bot.settings.get(message.guild, "bot_prefix")
    extras = [prefix_set] + forced_prefixes

    return commands.when_mentioned_or(*extras)(bot, message)
