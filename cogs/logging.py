# ⚠️ Warning, part of the code in that file comes from https://github.com/nerrixDE/simple-modlogs
# It's copied and licenced specifically for this project under the foillowing conditions:
# "You're allowed to use my code in your AGPL-Bot as long as you fufill all GPLv3 terms - just except same license, you can stick with AGPL"
# https://discordapp.com/channels/110373943822540800/468690756899438603/709861176506318959

import collections
import io
import typing
import datetime

import asyncio
import discord

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from discord.ext import commands

from cogs.helpers import context, checks
from cogs.helpers.hastebins import upload_text
from cogs.helpers.context import CustomContext

ATTACHMENTS_UPLOAD_CHANNEL_ID = 624129637928140802


async def save_attachments(bot: 'GetBeaned', message: discord.Message):
    if len(message.attachments) >= 1:
        attachments_upload_channel = bot.get_channel(ATTACHMENTS_UPLOAD_CHANNEL_ID)
        saved_attachments_files = []
        attachments_unsaved_urls = []
        total_files = len(message.attachments)
        saved_files = 0
        for i, attachment in enumerate(message.attachments):
            file = io.BytesIO()
            attachment: discord.Attachment
            try:
                await attachment.save(file, seek_begin=True, use_cached=True)  # Works most of the time
            except discord.HTTPException:
                try:
                    await attachment.save(file, seek_begin=True, use_cached=False)  # Almost never works, but worth a try!
                except discord.HTTPException:
                    attachments_unsaved_urls.append(attachment.url)
                    break  # Couldn't save
            saved_files += 1
            saved_attachments_files.append(discord.File(fp=file, filename=attachment.filename))
        if saved_files >= 0:
            try:
                saved = await attachments_upload_channel.send(
                    content=f"`[{saved_files}/{total_files}]` - Attachment(s) for message {message.id} on channel `[{message.channel.id}]` #{message.channel.name}, in guild `[{message.guild.id}]` {message.guild.name}",
                    files=saved_attachments_files)
            except discord.HTTPException:
                # Too large for the bot
                return [], [a.url for a in message.attachments]

            attachments_saved_urls = [a.url for a in saved.attachments]
        else:
            attachments_saved_urls = []
    else:
        return [], []

    return attachments_saved_urls, attachments_unsaved_urls


class Logging(commands.Cog):
    """
    Logging events.

    Here you'll find events that listen to message edition and deletion,
    and post the appropriate embeds in the appropriate channels if asked to by the guild settings
    """

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.api = bot.api
        self.snipes = bot.cache.get_cache("logging_deleted_messages", expire_after=7200, default=lambda: collections.deque(maxlen=15))  # channel: [message, message]

    async def perms_okay(self, channel: discord.TextChannel):
        wanted_permissions = discord.permissions.Permissions.none()
        wanted_permissions.update(
            send_messages=True,
            embed_links=True,
            attach_files=True,
        )

        my_permissions = channel.guild.me.permissions_in(channel)

        return my_permissions.is_strict_superset(wanted_permissions)

    async def get_logging_channel(self, guild: discord.Guild, pref: str):
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
        self.bot.logger.debug(f"Getting logging channel for {guild}, pref={pref}, channel_id={channel_id}, channel={channel}")

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
    async def on_bulk_message_delete(self, messages: typing.List[discord.Message]):
        """
        Handle bulk message deletions. However, older deleted messages that aren't in discord internal cache will not fire
        this event so we kinda "hope" that the messages weren't too old when they were deleted, and that they were in the cache

        This may log other bots
        """

        first_message = messages[0]

        if first_message.guild is None:
            return

        if "[getbeaned:disable_logging]" in str(first_message.channel.topic):
            return

        logging_channel = await self.get_logging_channel(first_message.guild, 'logs_delete_channel_id')

        if not logging_channel:
            return

        guild = first_message.guild

        channel = first_message.channel
        channel_id = channel.id

        bulky_messages_list = [f"Messages bulk-deleted on #{channel.name} (https://discordapp.com/channels/{guild.id}/{channel_id})\n",
                               f"Creation date :: Message ID :: [ID] Author - Content"]

        authors = set()

        for message in messages:
            author = message.author

            authors.add(author)

            bulky_messages_list.append(f"{message.created_at} :: {message.id} :: `[{author.id}]` {author.name}#{author.discriminator} \t - {message.content}")

        if await self.perms_okay(logging_channel):
            embed = discord.Embed(title=f"#{channel.name}",
                                  colour=discord.Colour.dark_red(),
                                  description=f"\nChannel: \t`[{channel_id}]` [#{channel.name}](https://discordapp.com/channels/{guild.id}/{channel_id}) \n"
                                              f"Authors: \t `{len(authors)}` \n"
                                              f"Messages: \t `{len(messages)}`"
                                  )

            embed.set_author(name="Messages deleted (in bulk)", url="https://getbeaned.me")  # , icon_url="ICON_URL_DELETE")

            embed.timestamp = first_message.created_at

            embed.set_footer(text="First message was created at",
                             icon_url="https://cdn.discordapp.com/avatars/492797767916191745/759b16c274c3cec8aef7cedd67014ac1.png?size=128")

            embed.add_field(name="Deleted messages list",
                            value=await upload_text("\n".join(bulky_messages_list)))

            await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, raw_message_update: discord.RawMessageUpdateEvent):
        """
        Handle **raw** message edits. ~~However, older messages that aren't in discord internal cache will not fire
        this event so we kinda "hope" that the message wasn't too old when it was edited, and that it was in the cache~~

        This doesn't logs other bots
        """

        message_id = raw_message_update.message_id
        channel_id = int(raw_message_update.data["channel_id"])  # TODO: In d.py 1.3.0, make that raw_message_update.channel_id

        new_content = raw_message_update.data.get("content", None)  # Embed may be partial, see doc.

        if not new_content:
            return

        if len(new_content) > 450:
            new_content = new_content[:450] + " [...]"

        if raw_message_update.cached_message:
            cached_message = True
            old_message = raw_message_update.cached_message
            channel = old_message.channel
            author = old_message.author

            old_content = old_message.content

        else:
            cached_message = False
            channel = self.bot.get_channel(channel_id)

            author = self.bot.get_user(int(raw_message_update.data["author"]["id"]))

            if author is None:
                return

        if channel is None or isinstance(channel, discord.abc.PrivateChannel):
            return

        if "[getbeaned:disable_logging]" in str(channel.topic):
            return

        guild = channel.guild

        if author.bot:
            return

        logging_channel = await self.get_logging_channel(guild, 'logs_edits_channel_id')

        if not logging_channel:
            return

        embed = discord.Embed(title=f"{author.name}#{author.discriminator}",
                              colour=discord.Colour.orange(),
                              url=f"https://getbeaned.me/users/{guild.id}/{author.id}",
                              description=f"\n[► View The Message](https://discordapp.com/channels/{guild.id}/{channel_id}/{message_id}).\n\n"
                                          f"Channel: \t`[{channel_id}]` [#{channel.name}](https://discordapp.com/channels/{guild.id}/{channel_id}) \n"
                                          f"Author: \t`[{author.id}]` {author.mention} \n"
                                          f"Message: \t`[{message_id}]`"
                              )

        embed.set_thumbnail(url=str(author.avatar_url))
        embed.set_author(name="Message edited", url="https://getbeaned.me")  # , icon_url="ICON_URL_EDIT")

        if cached_message:
            embed.timestamp = old_message.created_at

            embed.set_footer(text="Message was originally created at",
                             icon_url="https://cdn.discordapp.com/avatars/492797767916191745/759b16c274c3cec8aef7cedd67014ac1.png?size=128")

            if len(old_content) > 450:
                old_content = old_content[:450] + " [...] "
                if not old_message.author.bot:
                    old_content += "— Message too big to be shown here, full message available at " + await upload_text(old_message.content)

            embed.add_field(name="Original message",
                            value=old_content)

        embed.add_field(name="Edited message",
                        value=new_content)

        if not cached_message:
            embed.set_footer(text="The message original posting date is not available",
                             icon_url="https://cdn.discordapp.com/avatars/492797767916191745/759b16c274c3cec8aef7cedd67014ac1.png?size=128")
            embed.add_field(name="🙄",
                            value="The message was **not** in the internal bot cache, and only the edited message is able to be displayed. This often means that the message was posted too long ago.")

        if await self.perms_okay(channel):
            await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
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

        if len(message.content) == 0 and len(message.attachments) == 0:
            return

        self.snipes[message.channel].append(message)
        self.snipes.reset_expiry(message.channel)

        if "[getbeaned:disable_logging]" in str(message.channel.topic):
            return

        logging_channel = await self.get_logging_channel(message.guild, 'logs_delete_channel_id')

        if not logging_channel:
            return

        if len(message.attachments) >= 1:
            attachments_saved_urls, attachments_unsaved_urls = await save_attachments(self.bot, message)

            attachments_text = []
            if len(attachments_saved_urls) >= 1:
                attachments_text = ["\n- ".join(attachments_saved_urls)]
            if len(attachments_saved_urls) < len(message.attachments):
                attachments_text.append("The following attachments could **not** be saved by the bot: " + "\n- ".join(attachments_unsaved_urls))
            attachments_text = "\n".join(attachments_text)

        if len(message.content) > 450:
            content = message.content[:450] + " [...] "
            if not message.author.bot:
                content += "— Message too big to be shown here, full message available at " + await upload_text(message.content)
        elif len(message.content) == 0:
            content = f"The message contained no text, and {len(message.attachments)} attachments."

        else:
            content = message.content

        ctx = await self.bot.get_context(message, cls=context.CustomContext)
        ctx.logger.info(f"Logging message deletion")

        if await self.bot.settings.get(message.guild, 'logs_as_embed') and await self.perms_okay(logging_channel):
            author = message.author
            guild = message.guild
            channel = message.channel
            channel_id = channel.id
            message_id = message.id

            embed = discord.Embed(title=f"{author.name}#{author.discriminator}",
                                  colour=discord.Colour.red(),
                                  url=f"https://getbeaned.me/users/{guild.id}/{author.id}",
                                  description=f"\nChannel: \t`[{channel_id}]` [#{channel.name}](https://discordapp.com/channels/{guild.id}/{channel_id}) \n"
                                              f"Author: \t`[{author.id}]` {author.mention} \n"
                                              f"Message: \t`[{message_id}]`"
                                  )

            embed.set_thumbnail(url=str(author.avatar_url))
            embed.set_author(name="Message deleted", url="https://getbeaned.me")  # , icon_url="ICON_URL_DELETE")

            embed.timestamp = message.created_at

            embed.set_footer(text="Message was created at",
                             icon_url="https://cdn.discordapp.com/avatars/492797767916191745/759b16c274c3cec8aef7cedd67014ac1.png?size=128")

            embed.add_field(name="Deleted message content",
                            value=content)

            if len(message.attachments) >= 1:
                embed.add_field(name="Message attachments",
                                value=attachments_text)

            await logging_channel.send(embed=embed)

        else:
            textual_log = f"Message deleted | " \
                          f"By {message.author.name}#{message.author.discriminator}({message.author.id})\n" \
                          f"In {message.channel.mention}" \
                          f"**Content**:{content}"

            try:
                await logging_channel.send(textual_log)
            except discord.errors.Forbidden:
                ctx.logger.info(f"Couldn't log message deletion {message} (No perms)")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = await self.get_logging_channel(member.guild, 'logs_joins_channel_id')

        if not channel:
            return

        if await self.bot.settings.get(member.guild, 'logs_as_embed') and await self.perms_okay(channel):

            embed = discord.Embed(title=f"{member.name}#{member.discriminator}",
                                  colour=discord.Colour.green(),
                                  url=f"https://getbeaned.me/users/{member.guild.id}/{member.id}",
                                  description=f"Member: \t `[{member.id}]` {member.mention} \n"
                                  )

            embed.set_thumbnail(url=str(member.avatar_url))
            embed.set_author(name="Member joined", url="https://getbeaned.me")  # , icon_url="ICON_URL_DELETE")

            embed.timestamp = member.created_at

            embed.set_footer(text="Member created his account on",
                             icon_url="https://cdn.discordapp.com/avatars/492797767916191745/759b16c274c3cec8aef7cedd67014ac1.png?size=128")

            embed.add_field(name="Current member count",
                            value=str(member.guild.member_count))

            await channel.send(embed=embed)

        else:
            textual_log = f"Member Joined | {member.name}#{member.discriminator} (`{member.id}`)\n" \
                          f"**Current member count**: {member.guild.member_count}"

            try:
                await channel.send(textual_log)
            except discord.errors.Forbidden:
                self.bot.logger.info(f"Couldn't log user leave {member} (No perms)")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = await self.get_logging_channel(member.guild, 'logs_joins_channel_id')
        if not channel:
            return

        self.bot.logger.info(f"Logging user leave {member}")

        if await self.bot.settings.get(member.guild, 'logs_as_embed') and await self.perms_okay(channel):
            embed = discord.Embed(title=f"{member.name}#{member.discriminator}",
                                  colour=discord.Colour.dark_orange(),
                                  url=f"https://getbeaned.me/users/{member.guild.id}/{member.id}",
                                  description=f"Member: \t `[{member.id}]` {member.mention} \n"
                                              f"Joined: \t {str(member.joined_at)}\n"
                                              f"Roles: \t `{len(member.roles)}` : {', '.join([r.name for r in member.roles])}"
                                  )

            embed.set_thumbnail(url=str(member.avatar_url))
            embed.set_author(name="Member left/was kicked", url="https://getbeaned.me")  # , icon_url="ICON_URL_DELETE")

            embed.timestamp = member.created_at

            embed.set_footer(text="Member created his account on",
                             icon_url="https://cdn.discordapp.com/avatars/492797767916191745/759b16c274c3cec8aef7cedd67014ac1.png?size=128")

            embed.add_field(name="Current member count",
                            value=str(member.guild.member_count))

            await channel.send(embed=embed)
        else:

            textual_log = f"Member Left | {member.name}#{member.discriminator} (`{member.id}`)\n" \
                          f"**Current member count**: {member.guild.member_count}"
            try:
                await channel.send(textual_log)
            except discord.errors.Forbidden:
                self.bot.logger.info(f"Couldn't log user leave {member} (No perms)")

    @commands.Cog.listener()
    async def on_member_update(self, old: discord.Member, new: discord.Member):
        await asyncio.sleep(0.5)  # Wait for audit log to be created
        found_entry = None

        if old.nick != new.nick:
            try:
                async for entry in new.guild.audit_logs(limit=50, action=discord.AuditLogAction.member_update, after=datetime.datetime.utcnow() - datetime.timedelta(seconds=15),
                                                        oldest_first=False):
                    if entry.created_at < datetime.datetime.utcnow() - datetime.timedelta(seconds=10):
                        continue
                    if entry.target.id == new.id:
                        found_entry = entry
                        break
                found_entry: discord.AuditLogEntry
            except discord.Forbidden:
                pass

            # Nickname update
            channel = await self.get_logging_channel(old.guild, 'logs_member_edits_channel_id')

            if not channel:
                return

            self.bot.logger.info(f"Logging user edit {old}->{new}")

            if await self.bot.settings.get(old.guild, 'logs_as_embed') and await self.perms_okay(channel):

                embed = discord.Embed(title=f"{new.name}#{new.discriminator}",
                                      colour=discord.Colour.dark_orange(),
                                      url=f"https://getbeaned.me/users/{new.guild.id}/{new.id}",
                                      description=f"Member: \t `[{new.id}]` {new.mention} \n"
                                                  f"Old nickname: \t {old.nick}\n"
                                                  f"New nickname: \t {new.nick}"
                                      )
                if found_entry and found_entry.user.id != new.id:
                    embed.add_field(name="Responsible moderator", value=f"{found_entry.user.name}#{found_entry.user.discriminator} `[{found_entry.user.id}]`")

                embed.set_thumbnail(url=str(new.avatar_url))
                embed.set_author(name="Member changed nickname", url="https://getbeaned.me")  # , icon_url="ICON_URL_DELETE")

                embed.timestamp = new.joined_at

                embed.set_footer(text="Member joined on",
                                 icon_url="https://cdn.discordapp.com/avatars/492797767916191745/759b16c274c3cec8aef7cedd67014ac1.png?size=128")

                await channel.send(embed=embed)
            else:
                textual_log = f"Member Nickname Edited | {old.name}#{old.discriminator} (`{old.id}`)\n" \
                              f"**Old**: {old.nick}\n" \
                              f"**New**: {new.nick}"

                try:
                    await channel.send(textual_log)
                except discord.errors.Forbidden:
                    self.bot.logger.info(f"Couldn't log member update {old}->{new} (No perms)")

    @staticmethod
    async def snipe_as_embed(ctx: 'CustomContext', message: discord.Message):
        embed = discord.Embed()
        embed.title = f"Sniped message | {message.id}"
        embed.add_field(name="By", value=message.author.mention)
        embed.add_field(name="In", value=message.channel.mention)
        embed.description = message.content
        embed.set_footer(text=f"You can get more info about how automod treated this message with {ctx.prefix}automod_logs {message.id}")
        embed.timestamp = message.created_at
        await ctx.send(embed=embed)

    @staticmethod
    async def snipe_as_webhook(ctx: 'CustomContext', webhook: discord.Webhook, message: discord.Message):
        embed = discord.Embed()
        embed.title = f"Sniped message | {message.id}"
        embed.description = "This is a GetBeaned sniped message"
        embed.set_footer(text=f"You can get more info about how automod treated this message with {ctx.prefix}automod_logs {message.id}")
        embed.timestamp = message.created_at

        await webhook.send(discord.utils.escape_mentions(message.content), embed=embed)
        # await webhook.send(f"```\nThe message was created at {message.created_at}\nYou can get more info about how automod treated this message with {ctx.prefix}automod_logs {message.id}```")
        await webhook.delete()

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_minimal_permissions()
    @checks.have_required_level(2)
    async def snipe(self, ctx: 'CustomContext'):
        try:
            message = self.snipes[ctx.channel].pop()
        except IndexError:  # Nothing in deque
            await ctx.send("❌ Nothing to snipe")
            return

        avatar = await message.author.avatar_url.read()

        try:
            webhook = await ctx.channel.create_webhook(name=message.author.display_name, avatar=avatar, reason=f"Snipe command from {ctx.message.author.name}")
            await self.snipe_as_webhook(ctx, webhook, message)
        except discord.Forbidden:
            await self.snipe_as_embed(ctx, message)
            return


def setup(bot: 'GetBeaned'):
    bot.add_cog(Logging(bot))
