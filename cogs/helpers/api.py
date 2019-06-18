import asyncio
import json
from typing import Union

import aiohttp
import discord

from cogs.helpers.helpful_classes import FakeMember, LikeUser

with open("credentials.json", "r") as f:
    credentials = json.load(f)



API_URL = "https://getbeaned.me/api"

API_TOKEN = credentials["web_token"]

headers = {'Authorization': API_TOKEN}


class Api:
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    async def add_action_from_ctx(self, ctx, on, action_type, reason):
        if ctx.message.attachments:
            attachments_url = ctx.message.attachments[0].url
        else:
            attachments_url = ''
        res = await self.add_action(ctx.guild, on, action_type, reason, ctx.message.author, attachments_url)
        ctx.logger.debug(f"Got response from server : {res}")
        return res

        # await ctx.send(res)

    async def add_user(self, user:Union[discord.User, discord.Member, LikeUser, FakeMember]):

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
        await self.add_user(guild.owner)

        data = {'discord_id': guild.id,
                'discord_name': guild.name,
                'discord_icon_url': str(guild.icon_url) if guild.icon_url else f'https://cdn.discordapp.com/icons/{guild.id}.png',
                # Probably doesn't work
                'discord_created_at': str(guild.created_at),
                'discord_user_count': guild.member_count,
                'owner': guild.owner.id}
        # self.logger.debug(f"(add_guild) -> {data}")

        async with aiohttp.ClientSession() as cs:
            async with cs.post(API_URL + "/guilds/", data=data, headers=headers) as r:
                res = await r.json()
                # self.logger.debug(f"(add_guild) <- {res}")
                return res

    async def add_action(self, guild, user, action_type, reason, responsible_moderator, attachment='',
                         automod_logs=None):
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

    async def get_settings(self, guild):
        await self.add_guild(guild)
        guild_id = guild.id
        # self.logger.debug(f"(get_settings) -> {guild_id}")
        async with aiohttp.ClientSession() as cs:
            async with cs.get(API_URL + f"/settings/{guild_id}/", headers=headers) as r:
                res = await r.json()
                # self.logger.debug(f"(get_settings) <- {res}")
                return res

    async def set_settings(self, guild, setting, value):
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

    async def get_counters(self, guild, user):
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

    async def add_to_staff(self, guild, user, staff_type: str):
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
