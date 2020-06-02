import asyncio
import json
import typing
from datetime import datetime
from typing import Union, List

import aiohttp
import discord

from cogs.helpers.context import CustomContext
from cogs.helpers.helpful_classes import FakeMember, LikeUser

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

with open("credentials.json", "r") as f:
    credentials = json.load(f)

API_URL = "https://getbeaned.me/api"

API_TOKEN = credentials["web_token"]

headers = {'Authorization': API_TOKEN}


class Api:
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.logger = bot.logger

    async def add_action_from_ctx(self, ctx: CustomContext, on: Union[discord.User, discord.Member, LikeUser, FakeMember], action_type: str, reason: str):
        if ctx.message.attachments:
            attachments_url = ctx.message.attachments[0].url
        else:
            attachments_url = ''
        res = await self.add_action(ctx.guild, on, action_type, reason, ctx.message.author, attachments_url)
        ctx.logger.debug(f"Got response from server : {res}")
        return res

        # await ctx.send(res)

    async def add_user(self, user: Union[discord.User, discord.Member, LikeUser, FakeMember]):

        if hasattr(user, 'do_not_update'):
            do_not_update = user.do_not_update
        else:
            do_not_update = False

        new_headers = headers.copy()
        new_headers['update'] = str(not do_not_update)

        data = {'discord_bot': user.bot,
                'discord_id': user.id,
                'discord_name': user.name,
                'discord_discriminator': user.discriminator,
                'discord_avatar_url': str(user.avatar_url_as(static_format='png', size=1024)),
                'discord_default_avatar_url': str(user.default_avatar_url),
                }
        # self.logger.debug(f"(add_user) -> {data}")
        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + "/users/", data=data, headers=new_headers) as r:
                try:
                    res = await r.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    print(await r.text())
                    raise
                # self.logger.debug(f"(add_user) <- {res}")
                return res

    async def add_guild(self, guild):
        if guild.owner is None:
            owner = await guild.fetch_member(guild.owner_id)
        else:
            owner = guild.owner
        await self.add_user(owner)

        data = {'discord_id': guild.id,
                'discord_name': guild.name,
                'discord_icon_url': str(guild.icon_url) if guild.icon_url else f'https://cdn.discordapp.com/icons/{guild.id}.png',
                # Probably doesn't work
                'discord_created_at': str(guild.created_at),
                'discord_user_count': guild.member_count,
                'owner': guild.owner_id}
        # self.logger.debug(f"(add_guild) -> {data}")

        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + "/guilds/", data=data, headers=headers) as r:
                res = await r.json()
                # self.logger.debug(f"(add_guild) <- {res}")
                return res

    async def add_action(self, guild: discord.guild, user: Union[discord.User, discord.Member, LikeUser, FakeMember], action_type: str, reason: str,
                         responsible_moderator: Union[discord.User, discord.Member, LikeUser, FakeMember], attachment: str = '',
                         automod_logs: typing.Optional[str] = None):
        # Add the guild and the victim+moderator to the website... at the same time :O
        # https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
        await asyncio.gather(
            self.add_guild(guild),
            self.add_user(user),
            self.add_user(responsible_moderator),
        )

        data = {'guild': guild.id,
                'user': user.id,
                'action_type': action_type,
                'reason': reason if reason else 'No reason given.',
                'responsible_moderator': responsible_moderator.id,
                'attachment': attachment if attachment else '',
                'automod_logs': automod_logs if automod_logs else ''}

        self.logger.debug(f"(add_action) -> {data}")
        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + "/actions/", data=data, headers=headers) as r:
                res = await r.json()
                self.logger.debug(f"(add_action) <- {res}")
                return res

    async def get_settings(self, guild: discord.Guild):
        await self.add_guild(guild)
        guild_id = guild.id
        # self.logger.debug(f"(get_settings) -> {guild_id}")
        async with aiohttp.ClientSession() as cs:
            async with cs.get(API_URL + f"/settings/{guild_id}/", headers=headers) as r:
                res = await r.json()
                # self.logger.debug(f"(get_settings) <- {res}")
                return res

    async def set_settings(self, guild: discord.Guild, setting: str, value: str):
        await self.add_guild(guild)
        guild_id = guild.id
        data = {"setting": setting,
                "value": value}
        self.logger.debug(f"(set_settings) -> {guild_id}, data={data}")
        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + f"/settings/{guild_id}/", data=data, headers=headers) as r:
                res = await r.json()
                self.logger.debug(f"(set_settings) <- {res}")
                return res

    async def get_counters(self, guild: discord.Guild, user: discord.User):
        await self.add_guild(guild)
        await self.add_user(user)

        guild_id = guild.id
        user_id = user.id

        # self.logger.debug(f"(get_counters) -> g={guild_id}, u={user_id}")
        async with aiohttp.ClientSession() as cs:
            async with cs.get(API_URL + f"/users/{guild_id}/{user_id}/counters/", headers=headers) as r:
                res = await r.json()
                # self.logger.debug(f"(get_counters) <- {res}")
                return res

    async def add_to_staff(self, guild: discord.Guild, user: discord.User, staff_type: str):
        await self.add_user(user)
        await self.add_guild(guild)
        assert staff_type in ['banned', 'trusted', 'moderators', 'admins']

        guild_id = guild.id
        user_id = user.id

        data = {'position': staff_type,
                'user': user_id}

        # self.logger.debug(f"(add_to_staff) -> g={guild_id}, d={data}")

        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + f"/settings/{guild_id}/add_staff/", headers=headers, data=data) as r:
                try:
                    res = await r.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    print(await r.text())
                    raise
                # self.logger.debug(f"(add_to_staff) <- {res}")
                return res

    async def get_tasks(self):
        async with aiohttp.ClientSession() as cs:
            async with cs.get(API_URL + f"/tasks/", headers=headers) as r:
                try:
                    res = await r.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    print(await r.text())
                    raise
                # self.logger.debug(f"(get_tasks) <- {res}")
                return res

    async def create_task(self, task_type: str, arguments: str = None, execute_at: Union[str, datetime] = None):
        if arguments is not None and not isinstance(arguments, str):
            arguments = json.dumps(arguments)

        if execute_at is not None and not isinstance(arguments, str):
            execute_at = str(execute_at)

        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + f"/tasks/", headers=headers, data={"execute_at": execute_at, "task_type": task_type, "arguments": arguments}) as r:
                try:
                    res = await r.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    print(await r.text())
                    raise
                self.logger.debug(f"(create_task) <- {res}")
                return res

    async def complete_task(self, task_id: int):
        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + f"/tasks/{task_id}/complete", headers=headers) as r:
                try:
                    res = await r.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    print(await r.text())
                    raise
                self.logger.debug(f"(complete_task) <- {res}")
                return res

    async def save_roles(self, guild: discord.guild, user: Union[discord.Member, discord.User], roles: List[Union[discord.Role, int]]):
        await self.add_user(user)
        await self.add_guild(guild)

        roles_list = []

        for role in roles:
            if isinstance(role, discord.Role):
                roles_list.append(str(role.id))
            else:
                roles_list.append(str(int(role)))

        roles_list = ",".join(roles_list)

        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + f"/rolepersist/{guild.id}/{user.id}", headers=headers, data={"roles_ids": roles_list}) as r:
                try:
                    res = await r.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    print(await r.text())
                    raise
                self.logger.debug(f"(save_roles) <- {res}")
                return res

    async def get_stored_roles(self, guild: discord.Guild, user: Union[discord.Member, discord.User]) -> List[discord.Role]:
        await self.add_user(user)
        await self.add_guild(guild)

        async with aiohttp.ClientSession() as cs:
            async with cs.get(API_URL + f"/rolepersist/{guild.id}/{user.id}", headers=headers) as r:
                try:
                    res = await r.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    print(await r.text())
                    raise
                self.logger.debug(f"(get_stored_roles) <- {res}")

        roles = []

        if len(res["roles"]) > 0:
            for role_id in res["roles"].replace("\r\n", "").split(","):
                if len(role_id) > 0:
                    role = discord.utils.get(guild.roles, id=int(role_id))
                    if role:
                        roles.append(role)

        return roles
