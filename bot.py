#!/usr/bin/env python3.6
# This is GetBeaned, a discord mod bot with a beautiful web interface.
# **You have to use it with the rewrite version of discord.py**
# You can install it using
# > pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]
# > pip3.7 install -U "git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]"
# You also have to use python 3.7 to run this
# Have fun !
# The doc for d.py rewrite is here : http://discordpy.readthedocs.io/en/rewrite/index.html

print("Loading...")

# Importing the discord API warpper

print("Loading discord...")
import discord
print(f"Loaded discord {discord.version_info}")
# Load some essentials modules
print("Loading traceback...")

print("Loading collections...")

print("Loading json...")

print("Loading datetime...")

from cogs.helpers.init_logger import init_logger

print("Setting up logging")

base_logger, logger = init_logger()

# Setting up asyncio to use uvloop if possible, a faster implementation on the event loop
import asyncio

try:
    # noinspection PyUnresolvedReferences
    import uvloop
except ImportError:
    logger.warning("Using the not-so-fast default asyncio event loop. Consider installing uvloop.")
    pass
else:
    logger.info("Using the fast uvloop asyncio event loop")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger.debug("Importing the bot")

from cogs.helpers.GetBeaned import GetBeaned, get_prefix
logger.debug("Creating a bot instance of commands.AutoShardedBot")

intents = discord.Intents.none()
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.presences = True
intents.members = True

bot = GetBeaned(command_prefix=get_prefix, base_logger=base_logger, logger=logger, fetch_offline_members=False, chunk_guilds_at_startup=False, intents=intents, case_insensitive=True, max_messages=100000)
# bot.remove_command("help")

logger.debug("Loading cogs : ")

######################
#                 |  #
#   ADD COGS HERE |  #
#                 V  #
# ###############   ##

cogs = ['jishaku',
        'cogs.cache_control',
        'cogs.mod',
        'cogs.purge',
        'cogs.importation',
        'cogs.settings_commands',
        'cogs.stats',
        'cogs.automod',
        'cogs.meta',
        'cogs.logging',
        'cogs.help',
        'cogs.support',
        'cogs.dehoister',
        'cogs.autoinspect',
        'cogs.antiraid',
        'cogs.suggestions',
        'cogs.donators',
        'cogs.tasks',
        'cogs.role_persist',
        'cogs.inspector',
        'cogs.publisher',
        ]

for extension in cogs:
    try:
        bot.load_extension(extension)
        logger.debug(f"> {extension} loaded!")
    except Exception as e:
        logger.exception('> Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

logger.info("Everything seems fine, we are now connecting to discord.")

try:
    # bot.loop.set_debug(True)
    bot.loop.run_until_complete(bot.start(bot.token))
except KeyboardInterrupt:
    pass
finally:
    game = discord.Game(name=f"Restarting...")
    bot.loop.run_until_complete(bot.change_presence(status=discord.Status.dnd, activity=game))

    bot.loop.run_until_complete(bot.logout())

    bot.loop.run_until_complete(asyncio.sleep(3))
    bot.loop.close()
