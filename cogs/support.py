import asyncio
import datetime
import time
import typing

import discord
from discord import Color
from discord.ext import commands

from cogs.helpers import checks
from cogs.helpers.hastebins import upload_text
from cogs.helpers.level import get_level

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from cogs.helpers.context import CustomContext

PM_VIEWING_CHANNEL_ID = 557294214417874945


class Support(commands.Cog):
    """Cog for various support commands."""

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.conversations = bot.cache.get_cache("support_conversations", expire_after=3600, strict=True)
        self.temp_ignores = set()

    async def handle_private_message(self, received_message: discord.Message):
        if received_message.author.id in self.temp_ignores:
            return

        pm_channel = self.bot.get_channel(PM_VIEWING_CHANNEL_ID)
        user: discord.User = received_message.author

        if "discord.gg/" in received_message.content:
            await user.send("I've notice you just sent me an invite. This is **not** how you add a bot to a server. To invite GetBeaned, please click on this link: "
                            "https://discordapp.com/oauth2/authorize?client_id=492797767916191745&permissions=1878392007&scope=bot")
            await user.send("If you have any questions, join the support server -> https://discord.gg/cPbhK53")

        attachments_list = [e.url for e in received_message.attachments]

        embed = discord.Embed(title="Go to latest actions on the user", colour=discord.Colour(0x28d6ae), url=f"https://getbeaned.me/users/{user.id}",
                              description=f"{received_message.content[:1700]}", timestamp=datetime.datetime.now())

        embed.set_author(name=f"{user.name}", url="https://getbeaned.me", icon_url=f"{user.avatar_url}")
        embed.set_footer(text=f"{user.name}#{user.discriminator}", icon_url=f"{user.avatar_url}")

        if len(attachments_list) > 0:
            embed.add_field(name="📎 ", value=f"Attachments : {attachments_list}", inline=False)
        # embed.add_field(name="\U0001f507 ", value="Mute the user")
        # embed.add_field(name="\U0001f4de ", value="Join this conversation")

        sent_message = await pm_channel.send(content=f"{user.id}", embed=embed)

        emotes = [
            "\U0001f507",  # SPEAKER WITH CANCELLATION STROKE - :mute:
            # "\U0001f4f2",  # MOBILE PHONE WITH RIGHTWARDS ARROW AT LEFT - :calling:
            "\U0001f4de",  # TELEPHONE RECEIVER - :telephone_receiver:"
        ]

        for emote in emotes:
            await sent_message.add_reaction(emote)

        def check(reaction: discord.Reaction, user: discord.User):
            return str(reaction.emoji) in emotes and reaction.message.id == sent_message.id

        try:
            while True:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=3600.0, check=check)

                if user.id == self.bot.user.id:
                    continue

                if str(reaction.emoji) == "\U0001f507":  # Mute
                    self.temp_ignores.add(received_message.author.id)
                    await pm_channel.send(f"{user.mention}, you added {received_message.author.name} to the ignore list. "
                                          f"He'll be unignored if the bot restart or if you send him a PM thru the bot: `+pm {received_message.author.id} MESSAGE`")

                elif str(reaction.emoji) == "\U0001f4de":  # Answer
                    await pm_channel.send(f"{user.mention}, you are now talking to {received_message.author.name}.")
                    self.conversations[user.id] = received_message.author

        except asyncio.TimeoutError:
            await sent_message.clear_reactions()  # Nobody reacted :)

    async def handle_support_message(self, message: discord.Message):
        if message.content.startswith("#") or message.content.startswith("+"):
            return

        target_user = self.conversations.get(message.author.id, None)

        if target_user is None:
            return

        r = await self.send_pm(sender=message.author, receiver=target_user, message_content=message.content)

        if not r:
            await message.add_reaction("👌")
        else:
            await message.add_reaction("❌")
            pm_channel = self.bot.get_channel(PM_VIEWING_CHANNEL_ID)
            await pm_channel.send(r)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if not message.guild:
            await self.handle_private_message(message)

        elif message.channel.id == PM_VIEWING_CHANNEL_ID:
            await self.handle_support_message(message)

    @commands.command(aliases=["endpm"])
    @checks.have_required_level(8)
    async def end_pm(self, ctx: 'CustomContext'):
        self.conversations[ctx.author.id] = None
        await ctx.message.add_reaction("👌")

    @commands.command(aliases=["answer", "send_pm", "sendpm"])
    @checks.have_required_level(8)
    async def pm(self, ctx: 'CustomContext', user: discord.User, *, message_content: str):
        self.conversations[ctx.author.id] = user
        await self.send_pm(sender=ctx.author, receiver=user, message_content=message_content)

    async def send_pm(self, sender: discord.Member, receiver: discord.User, message_content: str):
        try:  # Remove from ignore list if replying
            self.temp_ignores.remove(receiver)
        except KeyError:
            pass

        try:
            await receiver.send(f"🐦 {sender.name}#{sender.discriminator}, a bot moderator, sent you the following message:\n>>> {message_content}")
        except Exception as e:
            return f"Error sending message to {sender.mention} ({sender.name}#{sender.discriminator}) : {e}"

        pm_channel = self.bot.get_channel(PM_VIEWING_CHANNEL_ID)

        await pm_channel.send(f"**{sender.name}#{sender.discriminator}** answered {receiver.mention} ({receiver.name}#{receiver.discriminator})\n>>> {message_content[:1900]}")

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(1)
    async def level(self, ctx: 'CustomContext', user: discord.Member = None):
        """
        Show your current access level

        -------------------------------------
        | Level | Description               |
        |-----------------------------------|
        | 10    | Bot owner (Eyesofcreeper) |
        | 09    | Reserved for future use   |
        | 08    | Bot moderators            |
        | 07    | Reserved for future use   |
        | 06    | Reserved for future use   |
        | 05    | Current server owner      |
        | 04    | Server administrator      |
        | 03    | Server moderator          |
        | 02    | Trusted users             |
        | 01    | Normal members            |
        | 00    | Users banned from the bot |
        -------------------------------------
        """

        if user is None:
            user = ctx.message.author

        l = await get_level(ctx, user)

        levels_names = {10: "Bot owner",
                        9: "Reserved for future use",
                        8: "Bot global-moderators",
                        7: "Reserved for future use",
                        6: "Reserved for future use",
                        5: "Server owner",
                        4: "Server administrator",
                        3: "Server moderator",
                        2: "Server trusted user",
                        1: "Member",
                        0: "Bot-banned"
                        }

        await ctx.send(f"Current level: {l} ({levels_names[l]})")

    async def safe_add_field(self, embed: discord.Embed, *, name: str, value: str, inline: bool = None, strip: bool = True):
        if len(value) > 1000:
            if strip:
                value = value.strip("`")

            value = await upload_text(value)
        embed.add_field(name=name, value=value, inline=inline)

    @commands.command(aliases=["message_info", "report_message", "message_report", "minfo"])
    @commands.guild_only()
    @checks.have_required_level(2)
    async def info_message(self, ctx: 'CustomContext', message_id: int):
        try:
            target_message: discord.Message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("❌ Message not found in the channel.")
            return False

        automod_cache = self.bot.cache.get_cache("automod_logs", expire_after=3600)

        embed = discord.Embed(timestamp=target_message.created_at,
                              title=f"Message report by {ctx.author.name}#{ctx.author.discriminator}")

        embed.set_author(name=f"{target_message.author.name}#{target_message.author.discriminator}", icon_url=target_message.author.avatar_url)
        await self.safe_add_field(embed, name="Content", value=target_message.content, inline=False, strip=False)

        if len(target_message.attachments) > 0:
            attachments = ", ".join(target_message.attachments)
            embed.add_field(name="Attachement(s)", value=attachments, inline=False)

        embed.add_field(name="Author ID", value=str(target_message.author.id), inline=True)
        embed.add_field(name="Channel ID", value=str(target_message.channel.id), inline=True)
        embed.add_field(name="Message ID", value=str(target_message.id), inline=True)

        embed.add_field(name="Author created at", value=str(target_message.author.created_at), inline=True)

        await self.safe_add_field(embed, name="Automod Logs", value="```\n" + automod_cache.get(message_id, "None stored :(") + "\n```", inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["permissions_checks", "permission_check", "bot_permissions_check"])
    @commands.guild_only()
    @checks.have_required_level(1)
    async def permissions_check(self, ctx: 'CustomContext', channel: discord.TextChannel = None):

        if not channel:
            channel = ctx.channel

        current_permissions: discord.Permissions = ctx.message.guild.me.permissions_in(channel)

        emojis = {
            True: "✅",
            False: "❌"
        }

        perms_check = []

        for permission in ["kick_members", "ban_members", "read_messages", "send_messages", "manage_messages", "embed_links", "attach_files",
                           "read_message_history", "external_emojis", "change_nickname", "view_audit_log", "add_reactions"]:
            have_perm = current_permissions.__getattribute__(permission)
            emoji = emojis[have_perm]
            perms_check.append(
                f"{emoji}\t{permission}"
            )

        await ctx.send("\n".join(perms_check))

    @commands.command(aliases=["hierarchy", "check_hierarchy"])
    @commands.guild_only()
    @checks.have_required_level(1)
    async def hierarchy_check(self, ctx: 'CustomContext', m: discord.Member):
        can_execute = ctx.author == ctx.guild.owner or \
                      ctx.author.top_role > m.top_role

        if can_execute:
            if m.top_role > ctx.guild.me.top_role:
                await ctx.send(f'❌ In the Discord Permissions system, the bot top role is lower or equal to the top role of the target.')
                return False
            await ctx.send("✅ Everything checks out!")
            return True
        else:
            await ctx.send('❌ In the Discord Permissions system, your top role is lower or equal to the top role of the target.')
            return False

    @commands.command(aliases=["bot_doctor", "support_check"])
    @commands.guild_only()
    @commands.cooldown(2, 60, commands.BucketType.guild)
    @checks.have_required_level(1)
    async def doctor(self, ctx: 'CustomContext'):
        waiting_message = await ctx.send("<a:loading:393852367751086090> Please wait, running `doctor` checks")  # <a:loading:393852367751086090> is a loading emoji
        t_1 = time.perf_counter()
        await ctx.trigger_typing()  # tell Discord that the bot is "typing", which is a very simple request
        t_2 = time.perf_counter()
        time_delta = round((t_2 - t_1) * 1000)  # calculate the time needed to trigger typing
        del self.bot.settings.settings_cache[ctx.guild]
        messages = {}
        message = []
        # Permissions
        wanted_permissions = discord.permissions.Permissions.none()
        wanted_permissions.update(
            kick_members=True,
            ban_members=True,
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            external_emojis=True,
            change_nickname=True,
            add_reactions=True
        )

        message.append("```diff")

        errored_in = []
        for channel in ctx.guild.channels:
            my_permissions = ctx.message.guild.me.permissions_in(channel)
            if not my_permissions.is_strict_superset(wanted_permissions):
                errored_in.append(channel)

        if len(errored_in) == 0:
            message.append("+ Everything checks out! No permissions problems")
        else:
            message.append(f"= The following channels have permissions problems, use the {ctx.prefix}bot_permissions_check command in them to see what's missing")
            message.extend(["- #" + channel.name for channel in errored_in])

        top_role = ctx.message.guild.me.top_role

        # Position isn't guaranteed to not have gaps
        # Discord pls

        message.append(f"= Bot top role is at position {top_role.position}/{ctx.guild.roles[-1].position} [higher is better] - "
                       f"Any user that have a role equal or higher to <{top_role.name}> can't be kicked/banned")
        message.append("```")

        embed_desc = "\n".join(message)
        if len(embed_desc) >= 1900:
            url = await upload_text(embed_desc)
            embed_desc = f"This was too long to show here (poor you), so here's a paste instead: {url}"

        messages["Bot Permissions"] = discord.Embed(description=embed_desc, color=Color.green() if len(errored_in) == 0 else Color.red())

        # Settings

        message = ["If a setting is enabled, the line will be in green. If it's disabled, the line will be red ```diff"]

        settings_char = {True: "+ ", False: "- "}

        guild = ctx.guild
        settings_to_check = {"automod_enable": "Automod",
                             "autotrigger_enable": "AutoTriggers (special automod rules to fight a specific kind of spam message — Require automod to be enabled too)",
                             "thresholds_enable": "Thresholds (automatic action when a users received X strikes)",
                             "logs_enable": "Logs",
                             "autoinspect_enable": "AutoInspect (Verification of new members that join your server)",
                             "rolepersist_enable": "RolePersist (VIP)"
                             }

        for setting, display_name in settings_to_check.items():
            setting_enabled = await self.bot.settings.get(guild, setting)

            message.append(settings_char[setting_enabled] + display_name)

        message.append(f"```\n To edit your settings, and see more of them, use the `{ctx.prefix}urls` command to see your server webpage, "
                       "then edit settings there (You may need to login first)\n")

        messages["Bot Settings"] = discord.Embed(description="\n".join(message), color=Color.dark_green())

        # Logs

        logs_enabled = await self.bot.settings.get(guild, "logs_enable")

        if logs_enabled:
            logs = {"logs_moderation_channel_id": "Moderation acts",
                    "logs_joins_channel_id": "Users joining/leaving",
                    "logs_rolepersist_channel_id": "Roles persist",
                    "logs_member_edits_channel_id": "Users edits",
                    "logs_edits_channel_id": "Message edits",
                    "logs_delete_channel_id": "Message deletions",
                    "logs_autoinspect_channel_id": "AutoInspect logs"}
            everything_good = True
            message = ["Logs are globally enabled on this server. The following specific logs are activated and configured: \n```diff"]
            for setting, display_name in logs.items():
                try:
                    setting_value = int(await self.bot.settings.get(guild, setting))
                except ValueError:
                    message.append(f"= {display_name} log (enabled but there is text in the ID field, I can't parse it)")
                else:
                    if setting_value == 0:
                        message.append(f"- {display_name} log")
                        everything_good = False
                    else:
                        channel_logged = discord.utils.get(guild.channels, id=setting_value)
                        if channel_logged:
                            message.append(f"+ {display_name} log (in #{channel_logged.name})")
                        else:
                            message.append(f"= {display_name} log (enabled but couldn't find the channel that goes by ID {setting_value})")
                            everything_good = False

            message.append("```")

            messages["Logs"] = discord.Embed(description="\n".join(message), color=Color.green() if everything_good else Color.dark_orange())

        message = []

        # Staff

        l = await get_level(ctx, ctx.author)

        levels_names = {10: "Bot owner",
                        9: "Reserved for future use",
                        8: "Bot global-moderators",
                        7: "Reserved for future use",
                        6: "Reserved for future use",
                        5: "Server owner",
                        4: "Server administrator",
                        3: "Server moderator",
                        2: "Server trusted user",
                        1: "Member",
                        0: "Bot-banned"
                        }

        message.append(f"Your current access level is `{l}` ({levels_names[l]}).")

        embed = discord.Embed(description="\n".join(message), color=Color.green() if l >= 3 else Color.orange())

        ids = await self.bot.settings.get(guild, 'permissions_admins')
        if len(ids) > 0:

            message = ["The following user(s) have been granted server **admin** (4) here "
                       "(This is not a complete list since it does **not** include people with the `administrator` permission) \n```diff"]
            for admin_id in ids:
                admin = discord.utils.get(guild.members, id=admin_id)
                if admin:
                    message.append(f"+ {admin.name}#{admin.discriminator} ({admin_id})")
                else:
                    role = discord.utils.get(guild.roles, id=admin_id)
                    if role:
                        message.append(f"+ (Role) {role.name} ({admin_id})")
                    else:
                        message.append(f"- User left the server ({admin_id})")
            message.append("```")

            embed.add_field(name="Server administrators", value="\n".join(message), inline=False)

        ids = await self.bot.settings.get(guild, 'permissions_moderators')
        if len(ids) > 0:
            message = ["The following user(s) have been granted server **moderator** (3) here "
                       "(This is not a complete list since it does **not** include people with the `ban_members` permission) \n```diff"]
            for mod_id in ids:
                mod = discord.utils.get(guild.members, id=mod_id)
                if mod:
                    message.append(f"+ {mod.name}#{mod.discriminator} ({mod_id})")
                else:
                    role = discord.utils.get(guild.roles, id=mod_id)
                    if role:
                        message.append(f"+ (Role) {role.name} ({mod_id})")
                    else:
                        message.append(f"- User left the server ({mod_id})")
            message.append("```")

            embed.add_field(name="Server moderators", value="\n".join(message), inline=False)

        ids = await self.bot.settings.get(guild, 'permissions_trusted')
        if len(ids) > 0:
            message = ["The following user(s) have been granted server **trusted** (2) here "
                       "(This is not a complete list since it does **not** include people with the `kick_members` permission) \n```diff"]
            for trusted_id in ids:
                trusted = discord.utils.get(guild.members, id=trusted_id)
                if trusted:
                    message.append(f"+ {trusted.name}#{trusted.discriminator} ({trusted_id})")
                else:
                    role = discord.utils.get(guild.roles, id=trusted_id)
                    if role:
                        message.append(f"+ (Role) {role.name} ({trusted_id})")
                    else:
                        message.append(f"- User left the server ({trusted_id})")
            message.append("```")

            embed.add_field(name="Trusted users", value="\n".join(message), inline=False)

        messages["Staff"] = embed

        embed = discord.Embed(description="This is stuff you can't do much about it, but just wait for the problems to go away if there are some. \n"
                                          "You might want to check https://status.discordapp.com for more information",
                              color=Color.green() if time_delta < 200 else Color.red())

        embed.add_field(name="Bot ping", value=f"{time_delta}ms")
        embed.add_field(name="Bot latency", value=f"{round(self.bot.latency * 1000)}ms")

        messages["Connexion"] = embed

        ok = True

        try:
            widget = await guild.widget()
        except discord.HTTPException:
            widget = None
            ok = False
        except KeyError:
            widget = None
            ok = True

        invite_code = await self.bot.settings.get(guild, 'invite_code')

        invite_error = False

        if not invite_code:
            ok = False
            invite_error = "No invite is set in your server settings. Please add it on the dashboard!"
        else:
            try:
                await self.bot.fetch_invite(invite_code)
            except discord.NotFound:
                invite_error = "The invite code was provided but is not working correctly. Please check that the invite is valid."
                ok = False
            except discord.HTTPException:
                invite_error = "There was an error reading your invite code. Please check that the invite is valid."
                ok = False



        embed = discord.Embed(description="Checking discord server settings since 1990",
                              color=Color.green() if ok else Color.red())

        embed.add_field(name="Widget enabled", value=f"Yes" if widget else "You should enable the server widget for it to show up properly on your server webpage. "
                                                                           "Sometimes, the bot can't detect your widget properly, in this case ignore this warning.")
        embed.add_field(name="Invite provided", value=f"Yes" if not invite_error else invite_error)

        messages["Server Settings"] = embed

        # Send everything
        for message_title, embed in messages.items():
            embed.title = message_title
            await ctx.send(embed=embed)
            # await ctx.trigger_typing()
            await asyncio.sleep(.8)

        await waiting_message.delete()


def setup(bot: 'GetBeaned'):
    bot.add_cog(Support(bot))
