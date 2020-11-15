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
STATUS_EMOJIS = {"offline": "<:offline:313956277237710868>",
                 "online": "<:online:313956277808005120>",
                 "idle": "<:away:313956277220802560>",
                 "dnd": "<:dnd:313956276893646850>",
                 "invisible": "<:invisible:313956277107556352>"}


async def inspect_member(ctx: 'CustomContext', inspected: typing.Union[discord.Member, discord.User]):
    icon_url = ctx.guild.me.avatar_url
    e = discord.Embed(title="GetBeaned inspection")

    if isinstance(inspected, discord.Member) and inspected.guild.id == ctx.guild.id:
        e.set_footer(text="Member is currently in server", icon_url=icon_url)
    elif ctx.guild.get_member(inspected.id):
        e.set_footer(text="User is currently in server", icon_url=icon_url)
    else:
        e.set_footer(text="User is not currently in server", icon_url=icon_url)

    e.add_field(name="Name", value=inspected.name, inline=True)
    e.add_field(name="Discriminator", value=inspected.discriminator, inline=True)
    e.add_field(name="ID", value=str(inspected.id), inline=True)

    if isinstance(inspected, discord.Member):
        e.add_field(name="(Desktop) Status", value=f"{STATUS_EMOJIS[inspected.desktop_status.name]} {inspected.desktop_status.name}", inline=True)
        e.add_field(name="(Mobile) Status", value=f"{STATUS_EMOJIS[inspected.mobile_status.name]} {inspected.mobile_status.name}", inline=True)
        e.add_field(name="Status", value=f"{STATUS_EMOJIS[inspected.status.name]} {inspected.status.name}", inline=True)

        human_delta = human_timedelta(inspected.joined_at, source=datetime.datetime.utcnow())
        e.add_field(name="Joined at", value=str(inspected.joined_at) + f" ({human_delta})", inline=False)

    human_delta = human_timedelta(inspected.created_at, source=datetime.datetime.utcnow())
    e.add_field(name="Account created at", value=str(inspected.created_at) + f" ({human_delta})", inline=False)

    e.add_field(name="Avatar URL", value=inspected.avatar_url, inline=False)

    e.add_field(name="Default Avatar URL", value=inspected.default_avatar_url, inline=False)

    if isinstance(inspected, discord.Member) and inspected.guild.id == ctx.guild.id:
        counters = await ctx.bot.api.get_counters(inspected.guild, inspected)
        for action_type in ['mute', 'note', 'warn', 'kick', 'ban']:
            if counters.get(action_type, 0) > 0:
                e.add_field(name=f"{action_type}s", value=str(counters[action_type]), inline=True)

    e.set_author(name=inspected.name, url=f"https://getbeaned.me/users/{inspected.id}", icon_url=inspected.avatar_url)

    e.set_image(url=str(inspected.avatar_url))

    await ctx.send(embed=e)


async def inspect_channel(ctx: 'CustomContext', inspected: typing.Union[discord.TextChannel, discord.VoiceChannel]):
    icon_url = ctx.guild.me.avatar_url
    e = discord.Embed(title="GetBeaned inspection")

    if ctx.guild.get_channel(inspected.id):
        e.set_footer(text="Channel is in this server", icon_url=icon_url)
    else:
        e.set_footer(text="Channel is not in this server", icon_url=icon_url)

    e.add_field(name="Name", value=inspected.name, inline=True)
    e.add_field(name="Type", value=inspected.type.name, inline=True)
    e.add_field(name="ID", value=str(inspected.id), inline=True)

    e.add_field(name="In Guild/Server", value=inspected.guild.name + f" `[{inspected.guild.id}]`", inline=False)

    human_delta = human_timedelta(inspected.created_at, source=datetime.datetime.utcnow())
    e.add_field(name="Created at", value=str(inspected.created_at) + f" ({human_delta})", inline=False)

    if isinstance(inspected, discord.VoiceChannel):
        e.add_field(name="User limit", value=str(inspected.user_limit), inline=True)
        e.add_field(name="Bitrate", value=str(inspected.bitrate / 1000) + " kbps", inline=True)
    elif isinstance(inspected, discord.TextChannel):
        e.add_field(name="Pins", value=str(len(await inspected.pins())), inline=True)
        e.add_field(name="Slowmode delay", value=str(inspected.slowmode_delay), inline=True)
        topic = inspected.topic
        if not topic:
            topic = "None"
        e.add_field(name="Topic", value=topic, inline=False)

    if inspected.category:
        e.add_field(name="Category", value=inspected.category.name, inline=False)
    await ctx.send(embed=e)


async def inspect_guild(ctx: 'CustomContext', inspected: discord.Guild):
    e = discord.Embed(title="GetBeaned inspection")

    e.add_field(name="Name", value=inspected.name, inline=True)

    bots_count = sum(m.bot for m in inspected.members)
    online = sum(m.status is discord.Status.online for m in inspected.members)
    e.add_field(name="Members", value=f"{inspected.member_count} ({online} online, {bots_count} bots)", inline=True)
    e.add_field(name="ID", value=str(inspected.id), inline=True)

    e.add_field(name="Channels", value=f"{len(inspected.channels)} total, {len(inspected.text_channels)} textual", inline=True)
    e.add_field(name="Categories", value=str(len(inspected.categories)), inline=True)
    e.add_field(name="Emojis", value=f"{len(inspected.emojis)}/{inspected.emoji_limit * 2}", inline=True)

    e.add_field(name="Region", value=inspected.region.name, inline=True)
    owner = inspected.owner
    e.add_field(name="Owner", value=f"{owner.name}#{owner.discriminator} `[{owner.id}]`", inline=True)
    bans = await inspected.bans()
    e.add_field(name="Bans", value=f"{len(bans)} currently", inline=True)

    human_delta = human_timedelta(inspected.created_at, source=datetime.datetime.utcnow())
    e.add_field(name="Created at", value=str(inspected.created_at) + f" ({human_delta})", inline=True)

    if inspected.me:
        human_delta = human_timedelta(inspected.me.joined_at, source=datetime.datetime.utcnow())
        e.add_field(name="Joined at", value=str(inspected.me.joined_at) + f" ({human_delta})", inline=True)

    icon_url = str(inspected.icon_url)
    if not icon_url:
        icon_url = "None"

    e.add_field(name="Icon URL", value=icon_url, inline=False)

    icon_url = ctx.guild.me.avatar_url
    if ctx.guild.id == inspected.id:
        e.set_footer(text="You are inspecting the guild you are in", icon_url=icon_url)
    else:
        e.set_footer(text="This is another guild you are inspecting", icon_url=icon_url)

    e.set_image(url=str(inspected.icon_url))

    await ctx.send(embed=e)


async def inspect_emoji(ctx: 'CustomContext', inspected: discord.Emoji):
    e = discord.Embed(title="GetBeaned inspection")

    e.add_field(name="Name", value=inspected.name, inline=True)
    e.add_field(name="Representation", value=str(inspected), inline=True)
    e.add_field(name="ID", value=str(inspected.id), inline=True)

    e.add_field(name="Animated", value=str(inspected.animated), inline=True)
    e.add_field(name="Available", value=str(inspected.available), inline=True)
    e.add_field(name="Managed", value=str(inspected.managed), inline=True)

    e.add_field(name="Guild", value=f"{inspected.guild.name} `[{inspected.guild_id}]`", inline=False)

    human_delta = human_timedelta(inspected.created_at, source=datetime.datetime.utcnow())
    e.add_field(name="Created at", value=str(inspected.created_at) + f" ({human_delta})", inline=False)

    e.add_field(name="URL", value=str(inspected.url), inline=False)

    icon_url = ctx.guild.me.avatar_url
    if ctx.guild.id == inspected.guild_id:
        e.set_footer(text="Emoji is in this Guild", icon_url=icon_url)
    else:
        e.set_footer(text="Emoji is in another Guild", icon_url=icon_url)

    e.set_image(url=str(inspected.url))

    await ctx.send(embed=e)


async def inspect_message(ctx: 'CustomContext', inspected: discord.Message):
    e = discord.Embed(title="GetBeaned inspection")

    e.add_field(name="Author", value=f"{inspected.author.name}#{inspected.author.discriminator} `[{inspected.author.id}]`", inline=True)
    e.add_field(name="Channel", value=f"{inspected.channel.name} `[{inspected.channel.id}]`", inline=True)
    e.add_field(name="Guild", value=f"{inspected.guild.name} `[{inspected.guild.id}]`", inline=True)

    e.add_field(name="Content", value=str(inspected.content)[:1000], inline=False)

    human_delta = human_timedelta(inspected.created_at, source=datetime.datetime.utcnow())
    e.add_field(name="Created at", value=str(inspected.created_at) + f" ({human_delta})", inline=False)
    e.add_field(name="Attachments", value=str([a.url for a in inspected.attachments]), inline=False)

    icon_url = ctx.guild.me.avatar_url
    if ctx.channel.id == inspected.channel.id:
        e.set_footer(text="Message is in this Channel", icon_url=icon_url)
    elif ctx.guild.id == inspected.guild.id:
        e.set_footer(text="Message is in this Guild", icon_url=icon_url)
    else:
        e.set_footer(text="Message is in another Guild", icon_url=icon_url)

    e.set_image(url=str(inspected.author.avatar_url))

    await ctx.send(embed=e)


async def inspect_invite(ctx: 'CustomContext', inspected: discord.Invite):
    e = discord.Embed(title="GetBeaned inspection")
    e.description = f"Depending on the invite, some fields here may have a value of None. That's because the bot doesn't know about them."
    e.add_field(name="Guild", value=f"{inspected.guild.name} `[{inspected.guild.id}]`", inline=False)

    if inspected.channel:
        e.add_field(name="Channel", value=f"{inspected.channel.name} `[{inspected.channel.id}]`", inline=False)
    else:
        e.add_field(name="Channel", value=f"{inspected.channel}", inline=False)

    if inspected.inviter:
        e.add_field(name="Inviter", value=f"{inspected.inviter.name}#{inspected.inviter.discriminator} `[{inspected.inviter.id}]`", inline=False)
    else:
        e.add_field(name="Inviter", value=f"{inspected.inviter}", inline=False)

    e.add_field(name="Members", value=f"{inspected.approximate_member_count}", inline=True)
    e.add_field(name="Online members", value=f"{inspected.approximate_presence_count}", inline=True)
    e.add_field(name="Uses", value=f"{inspected.uses}/{inspected.max_uses}", inline=True)

    e.add_field(name="Revoked", value=f"{inspected.revoked}", inline=True)
    e.add_field(name="Temporary", value=f"{inspected.temporary}", inline=True)
    e.add_field(name="URL", value=f"{inspected.url}", inline=False)

    if inspected.created_at:
        human_delta = human_timedelta(inspected.created_at, source=datetime.datetime.utcnow())
        e.add_field(name="Created at", value=str(inspected.created_at) + f" ({human_delta})", inline=False)
    else:
        e.add_field(name="Created at", value=str(inspected.created_at), inline=False)

    icon_url = ctx.guild.me.avatar_url
    if ctx.channel.id == inspected.channel.id:
        e.set_footer(text="Invite is for this Channel", icon_url=icon_url)
    elif ctx.guild.id == inspected.guild.id:
        e.set_footer(text="Invite is for this Guild", icon_url=icon_url)
    else:
        e.set_footer(text="Invite is for another Guild", icon_url=icon_url)

    await ctx.send(embed=e)


class Inspector(commands.Cog):

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.api = bot.api

    async def universal_converter(self, ctx: 'CustomContext', inspected: int) -> typing.Union[discord.Guild, discord.Emoji, discord.Message, discord.User,
                                                                                              discord.TextChannel, discord.VoiceChannel]:
        # Maybe it's a guild ID, or an user ID we don't have in cache, try everything, but since fetch_user is ratelimited, try that one after everything
        maybe_guild = self.bot.get_guild(inspected)
        if maybe_guild:
            return maybe_guild

        maybe_channel = self.bot.get_channel(inspected)
        if maybe_channel and not any([isinstance(maybe_channel, t) for t in [discord.StoreChannel, discord.DMChannel, discord.GroupChannel, discord.CategoryChannel]]):
            return maybe_channel

        maybe_emoji = self.bot.get_emoji(inspected)
        if maybe_emoji:
            return maybe_emoji

        maybe_message = discord.utils.get(self.bot.cached_messages, id=inspected)
        if maybe_message:
            return maybe_message

        # These are "expensive" API calls to make, but we exhausted the cache
        # Any user on Discord
        try:
            return await self.bot.fetch_user(inspected)
        except discord.NotFound:
            pass

        # Check for an older message in that channel
        try:
            return await ctx.channel.fetch_message(inspected)
        except discord.NotFound:
            pass

        raise discord.ext.commands.errors.BadArgument("Oops, the ID given does not match anything I can convert to. Double check that and try again.")

    @commands.command(aliases=["inspector"])
    @commands.guild_only()
    @checks.have_required_level(2)
    async def inspect(self, ctx: 'CustomContext', inspected: typing.Union[discord.Member, discord.User, discord.TextChannel, discord.VoiceChannel, int, str]):
        """Inspect an object and return properties about it..."""
        if isinstance(inspected, int):
            inspected = await self.universal_converter(ctx, inspected)

        if isinstance(inspected, discord.Member) or isinstance(inspected, discord.User):
            return await inspect_member(ctx, inspected)

        elif isinstance(inspected, discord.TextChannel) or isinstance(inspected, discord.VoiceChannel):
            return await inspect_channel(ctx, inspected)

        elif isinstance(inspected, discord.Guild):
            return await inspect_guild(ctx, inspected)

        elif isinstance(inspected, discord.Emoji):
            return await inspect_emoji(ctx, inspected)

        elif isinstance(inspected, discord.Message):
            return await inspect_message(ctx, inspected)

        elif isinstance(inspected, str):
            # Maybe an invite code
            try:
                return await inspect_invite(ctx, await self.bot.fetch_invite(inspected, with_counts=True))
            except discord.NotFound:
                pass
        # there was a bug that allowed any role to be mentioned
        # disable all mentions here that way you can't exploit this to ping everyone or a certain role
        await ctx.send(f"Type: {type(inspected)}, Str:{str(inspected)}",
                       allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))


def setup(bot: 'GetBeaned'):
    bot.add_cog(Inspector(bot))
