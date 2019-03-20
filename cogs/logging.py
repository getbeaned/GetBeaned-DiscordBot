import collections
import datetime

import discord
from discord.ext import commands

from cogs.helpers import context, checks


class Logging(commands.Cog):
    """
    Logging events.

    Here you'll find events that listen to message edition and deletion,
    and post the appropriate embeds in the appropriate channels if asked to by the guild settings
    """

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.snipes = collections.defaultdict(lambda: collections.deque(maxlen=5)) # channel: [message, message]

    async def get_logging_channel(self, guild, pref):
        # Beware to see if the channel id is actually in the same server (to compare, we will see if the current server
        # owner is the same as the one in the target channel). If yes, even if it's not the same server, we will allow
        # logging there

        if not await self.bot.settings.get(guild, 'logs_enable'):
            return None

        channel_id = int(await self.bot.settings.get(guild, pref))

        if channel_id == 0:
            # That would be handled later but no need to pass thru discord API if it's clearly disabled.
            return None

        channel = self.bot.get_channel(channel_id)

        if not channel:
            self.bot.logger.warning(f"There is something fishy going on with guild={guild.id}! Their {pref}="
                                    f"{channel_id} can't be found!")
            return None

        elif not channel.guild.owner == guild.owner:
            self.bot.logger.warning(f"There is something fishy going on with guild={guild.id}! Their {pref}="
                                    f"{channel_id} don't belong to them!")
            return None


        else:
            return channel

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """
        Handle message deletions. However, older deleted messages that aren't in discord internal cache will not fire
        this event so we kinda "hope" that the message wasn't too old when it was deleted, and that it was in the cache

        This dosen't logs other bots
        """

        if message.guild is None:
            return

        if message.author.bot:
            return

        if not message.type == discord.MessageType.default:
            return

        self.snipes[message.channel].append(message)

        channel = await self.get_logging_channel(message.guild, 'logs_delete_channel_id')

        if not channel:
            return

        ctx = await self.bot.get_context(message, cls=context.CustomContext)
        ctx.logger.info(f"Logging message deletion")

        if await self.bot.settings.get(message.guild, 'logs_as_embed'):

            embed = discord.Embed()
            if message.attachments:
                embed.add_field(name="Attachment", value=message.attachments[0].url)

            embed.colour = discord.colour.Color.red()

            embed.title = f"Message deleted | By {message.author.name}({message.author.id})"
            embed.description = message.content
            embed.add_field(name="Channel", value=message.channel.mention, inline=False)


            embed.set_author(name=self.bot.user.name)

            embed.timestamp = message.created_at

            await channel.send(embed=embed)

        else:
            textual_log = f"Message deleted | " \
                f"By {message.author.name}#{message.author.discriminator}({message.author.id})\n" \
                f"In {message.channel.mention}"\
                f"**Content**:{message.content}"

            await channel.send(textual_log)

    @commands.Cog.listener()
    async def on_message_edit(self, old, new):
        """
        Handle message edits. However, older messages that aren't in discord internal cache will not fire
        this event so we kinda "hope" that the message wasn't too old when it was edited, and that it was in the cache

        This dosen't logs other bots
        """

        if old.guild is None:
            return

        if old.author.bot:
            return

        if old.content == new.content:
            return

        channel = await self.get_logging_channel(old.guild, 'logs_edits_channel_id')

        if not channel:
            return

        ctx = await self.bot.get_context(new, cls=context.CustomContext)
        ctx.logger.info(f"Logging message edition")

        if await self.bot.settings.get(old.guild, 'logs_as_embed'):
            embed = discord.Embed()

            embed.colour = discord.colour.Color.orange()

            embed.title = f"Message edited | By {old.author.name}({old.author.id})"
            embed.description = new.content[:1023]

            embed.add_field(name="Old content", value=old.content[:1023], inline=False)

            embed.set_author(name=self.bot.user.name)

            embed.timestamp = datetime.datetime.now()

            await channel.send(embed=embed)

        else:
            textual_log = f"Message edited | " \
                f"By {old.author.name}#{old.author.discriminator}({old.author.id})\n" \
                f"**Old**:{old.content}\n" \
                f"**New**:{new.content}"

            await channel.send(textual_log)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.get_logging_channel(member.guild, 'logs_joins_channel_id')

        if not channel:
            return

        self.bot.logger.info(f"Logging user join for guild:{member.guild.id}")

        if await self.bot.settings.get(member.guild, 'logs_as_embed'):
            embed = discord.Embed()

            embed.colour = discord.colour.Color.green()

            embed.title = f"New Member | {member.name}({member.id})"

            embed.add_field(name="Current member count", value=str(member.guild.member_count))

            embed.set_author(name=self.bot.user.name)

            embed.timestamp = datetime.datetime.now()

            await channel.send(embed=embed)

        else:
            textual_log = f"Member Joined | {member.name}#{member.discriminator} (`{member.id}`)\n" \
                f"**Current member count**: {member.guild.member_count}"

            await channel.send(textual_log)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = await self.get_logging_channel(member.guild, 'logs_joins_channel_id')


        if not channel:
            return

        self.bot.logger.info(f"Logging user leave for guild:{member.guild.id}")

        if await self.bot.settings.get(member.guild, 'logs_as_embed'):
            embed = discord.Embed()

            embed.colour = discord.colour.Color.red()

            embed.title = f"Member Left | {member.name}({member.id})"

            embed.add_field(name="Current member count", value=str(member.guild.member_count))

            embed.set_author(name=self.bot.user.name)

            embed.timestamp = datetime.datetime.now()

            await channel.send(embed=embed)
        else:
            textual_log = f"Member Left | {member.name}#{member.discriminator} (`{member.id}`)\n" \
                f"**Current member count**: {member.guild.member_count}"

            await channel.send(textual_log)

    @commands.Cog.listener()
    async def on_member_update(self, old, new):

        if old.nick != new.nick:
            # Nickname update
            channel = await self.get_logging_channel(old.guild, 'logs_member_edits_channel_id')

            if not channel:
                return

            self.bot.logger.info(f"Logging user edit for guild:{old.guild.id}")

            if await self.bot.settings.get(old.guild, 'logs_as_embed'):
                embed = discord.Embed()

                embed.colour = discord.colour.Color.red()

                embed.title = f"Member Nickname Change | {old.name}({old.id})"

                embed.add_field(name="Old nickname", value=old.nick)
                embed.add_field(name="New nickname", value=new.nick)

                embed.set_author(name=self.bot.user.name)

                embed.timestamp = datetime.datetime.now()

                await channel.send(embed=embed)

            else:
                textual_log = f"Member Nickname Edited | {old.name}#{old.discriminator} (`{old.id}`)\n" \
                    f"**Old**: {old.nick}\n" \
                    f"**New**: {new.nick}"

                await channel.send(textual_log)

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_minimal_permissions()
    @checks.have_required_level(2)
    async def snipe(self, ctx):
        try:
            message = self.snipes[ctx.channel].pop()
        except IndexError:  # Nothing in deque
            await ctx.send("❌ Nothing to snipe")
            return

        embed = discord.Embed()
        embed.title = f"Sniped message | {message.id}"
        embed.add_field(name="By", value=message.author.mention)
        embed.add_field(name="In", value=message.channel.mention)
        embed.description = message.content
        embed.set_footer(text=f"You can get more info about how automod treated this message with {ctx.prefix}automod_logs {message.id}")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Logging(bot))
