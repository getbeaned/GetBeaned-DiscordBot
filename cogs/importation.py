import typing

import discord
from discord.ext import commands

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from cogs.helpers import checks
from cogs.helpers.helpful_classes import LikeUser
from cogs.helpers.context import CustomContext


class Importation(commands.Cog):

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.api = bot.api

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(4)
    @checks.bot_have_minimal_permissions()
    async def import_bans(self, ctx: 'CustomContext'):
        """
        Import bans from the server banlist. If possible and available, also include the reason from the audit logs.

        This is only available to servers administrators, and can only be done once per guild.
        :param ctx:
        :return:
        """

        if await self.bot.settings.get(ctx.guild, 'imported_bans'):
            await ctx.send("You already imported your guild bans. "
                           "If you think this is an error, join the support server and ask!")
            return
        else:
            await self.bot.settings.set(ctx.guild, 'imported_bans', True)

        await ctx.send(f"Doing that, it may take a long time, please wait!")

        bans = await ctx.guild.bans()

        i = 0
        t = len(bans)
        for ban in bans:

            user = ban.user
            reason = ban.reason

            if not reason:
                reason = "No reason was provided in the audit logs"

            await self.api.add_action(ctx.guild, user, 'ban', reason,
                                      responsible_moderator=LikeUser(did=0, name="BanList Import", guild=ctx.guild))
            i += 1

        await ctx.send(f"{i}/{t} bans imported from the server ban list.")

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(4)
    @checks.bot_have_permissions()
    @commands.cooldown(rate=2, per=300, type=commands.BucketType.guild)
    async def create_muted_role(self, ctx: 'CustomContext'):
        """
        Create or update the muted role to disallow anyone with it to talk in any channel.
        """

        ROLE_NAME = "GetBeaned_muted"
        REASON = f"create_muted_role command invoked by {ctx.message.author.name}"

        current_permissions = ctx.message.guild.me.permissions_in(ctx.channel)

        if not current_permissions.manage_roles:
            await ctx.send(f"To run this, I additionally need the `manage_roles` permission, because I'll create/update the {ROLE_NAME} role.")
            return False

        if not current_permissions.manage_channels:
            await ctx.send(f"To run this, I additionally need the `manage_channels` permission, because I'll create/update the {ROLE_NAME} role.")
            return False

        logs_content = ["Creating the muted role, please wait", "Permissions check passed"]

        logs_message = await ctx.send("Creating the muted role, please wait")

        muted_role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)

        if not muted_role:
            logs_content.append("Couldn't find the muted role, creating it...")
            muted_role = await ctx.guild.create_role(name=ROLE_NAME, reason=REASON)

        logs_content.append(f"The muted role ID is {muted_role.id}")

        await logs_message.edit(content="```" + '\n'.join(logs_content) + "```")

        text_overwrite = discord.PermissionOverwrite()
        text_overwrite.update(send_messages=False, add_reactions=False, create_instant_invite=False)

        voice_overwrite = discord.PermissionOverwrite()
        voice_overwrite.update(speak=False, create_instant_invite=False)

        logs_content.append("Adding a PermissionOverwrite into the server channels :")
        for channel in ctx.guild.channels:
            current_channel_permissions = ctx.message.guild.me.permissions_in(channel)
            if not isinstance(channel, discord.TextChannel) and not isinstance(channel, discord.VoiceChannel):
                logs_content.append(f"\tS #{channel.name} (not a text or voicechannel)")
                continue

            if not current_channel_permissions.manage_roles or not current_channel_permissions.manage_channels:
                logs_content.append(f"\tS #{channel.name} (no permissions there)")
                continue

            if isinstance(channel, discord.TextChannel):
                await channel.set_permissions(muted_role, overwrite=None, reason=REASON)
                await channel.set_permissions(muted_role, overwrite=text_overwrite, reason=REASON)
                logs_content.append(f"\tT #{channel.name}")
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(muted_role, overwrite=None, reason=REASON)
                await channel.set_permissions(muted_role, overwrite=voice_overwrite, reason=REASON)
                logs_content.append(f"\tV #{channel.name}")

        await logs_message.edit(content="```" + '\n'.join(logs_content)[:1800] + "```", delete_after=60)
        await ctx.send("The muted role has been successfully created/updated.")


def setup(bot: 'GetBeaned'):
    bot.add_cog(Importation(bot))
