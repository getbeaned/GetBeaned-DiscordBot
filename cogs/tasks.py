import json
import typing

import discord
from discord.ext import tasks, commands

from cogs.helpers.actions import full_process, unban, unmute
from cogs.helpers.helpful_classes import LikeUser, FakeMember

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned


class Tasks(commands.Cog):
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.run_tasks.start()
        self.tasks_mapping = {
            "refresh_user": self.refresh_user,
            "unmute": self.unmute_task,
            "unban": self.unban_task,
        }

    def cog_unload(self):
        self.run_tasks.stop()

    async def unmute_task(self, task: dict):
        arguments = json.loads(task['arguments'])  # {"target": 514557845111570447, "guild": 512328935304855555, "reason": "Time is up (1 week, 2 days and 23 hours)"}
        guild_id = arguments["guild"]

        guild: discord.Guild = self.bot.get_guild(guild_id)

        if guild:
            member = guild.get_member(arguments["target"])
            if member:
                tasks_user = LikeUser(did=5, name="DoItLater", guild=guild)
                act = await full_process(self.bot, unmute, member, tasks_user, arguments["reason"], automod_logs=f"Task number #{task['id']}")
                return True

    async def unban_task(self, task: dict):
        arguments = json.loads(task['arguments'])  # {"target": 514557845111570447, "guild": 512328935304855555, "reason": "Time is up (1 week, 2 days and 23 hours)"}
        guild_id = arguments["guild"]

        guild: discord.Guild = self.bot.get_guild(guild_id)

        if guild:
            user = await self.bot.fetch_user(int(arguments["target"]))

            if user:
                if not user.id in [b.user.id for b in await guild.bans()]:
                    return True  # Already unbanned

                fake_member = FakeMember(user, guild)

                tasks_user = LikeUser(did=5, name="DoItLater", guild=guild)
                act = await full_process(self.bot, unban, fake_member, tasks_user, arguments["reason"], automod_logs=f"Task number #{task['id']}")
                return True

        # Failed because no such guild/user
        return True  # Anyway

    async def refresh_user(self, task: dict):
        user = self.bot.get_user(int(task["arguments"]))

        if user is None:
            try:
                user = await self.bot.fetch_user(int(task["arguments"]))
            except discord.errors.NotFound:
                self.bot.logger.warning(f"Completing task #{task['id']} failed. User not found.")
                return True  # Returning true anyway

        if user is not None:
            await self.bot.api.add_user(user)
            return True
        else:
            self.bot.logger.warning(f"Completing task #{task['id']} failed. User not found.")
            return True  # Returning true anyway

    async def dispatch_task(self, task: dict):
        self.bot.logger.info(f"Running task #{task['id']}...")
        self.bot.logger.debug(str(task))

        task_type = task["type"]

        try:
            res = await self.tasks_mapping[task_type](task)
            self.bot.logger.debug(f"Ran task #{task['id']}, result is {res}")
            if res is not False:  # So if res is None, it'll still return True
                return True
            else:
                return False
        except KeyError:
            self.bot.logger.warning(f"Unsupported task #{task['id']}, type is {task['type']}")
            return False  # Unsupported task type

    @tasks.loop(minutes=1)
    async def run_tasks(self):
        try:
            #self.bot.logger.info("Cleaning up cache")
            tasks = await self.bot.api.get_tasks()
            self.bot.logger.debug(f"Got task list: {tasks}")
            for task in tasks:
                res = await self.dispatch_task(task)

                if res:
                    self.bot.logger.info(f"Completed task #{task['id']}")
                    await self.bot.api.complete_task(task["id"])
                else:
                    self.bot.logger.warning(f"Completing task #{task['id']} failed. res={res}")
        except Exception as e:
            self.bot.logger.exception(f"Failed in tasks loop...")
            raise


    @run_tasks.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("We are running tasks.")


def setup(bot: 'GetBeaned'):
    tasks = Tasks(bot)
    bot.add_cog(tasks)
