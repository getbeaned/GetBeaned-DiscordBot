import datetime
import typing

import discord
from discord.ext import commands

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned



class RolePersist(commands.Cog):
    """
    RolePersist
    """

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.api = bot.api

    async def is_role_persist_enabled(self, guild: discord.Guild):
        return await self.bot.settings.get(guild, "rolepersist_enable") and await self.bot.settings.get(guild, "vip")

    async def get_restorable_roles(self, guild: discord.Guild, roles: typing.List[discord.Role]):
        my_top_role = guild.me.top_role

        restorable_roles = []
        for role in roles:
            if role < my_top_role:
                restorable_roles.append(my_top_role)

    async def log_role_persist(self, guild: discord.Guild, member: discord.Member, roles_to_give: typing.List[discord.Role]):
        roles_to_give_names = [r.name for r in roles_to_give]
        roles_to_give_mentions = [r.mention for r in roles_to_give]

        reason = f"Restoring roles for {member.name}#{member.discriminator} in {guild}: {len(roles_to_give)} roles to give: {roles_to_give_names}"
        self.bot.logger.info(reason)

        logging_channel = await self.bot.get_cog('Logging').get_logging_channel(member.guild, "logs_rolepersist_channel_id")

        if not logging_channel:
            return 'No logging channel configured for RolePersist.'
        if not await self.bot.get_cog('Logging').perms_okay(logging_channel):
            return 'No permissions to log'
        embed = discord.Embed(title=f"{member.name}#{member.discriminator} joined",
                              colour=discord.Colour.dark_blue(),
                              description=f"Added {len(roles_to_give)} roles\n"
                                          f"{', '.join(roles_to_give_mentions)}"
                              )

        embed.set_author(name="Roles Persisted", url="https://getbeaned.me")  # , icon_url="ICON_URL_DELETE")

        embed.timestamp = datetime.datetime.utcnow()

        embed.set_footer(text="Roles restored at",
                         icon_url="https://cdn.discordapp.com/avatars/492797767916191745/759b16c274c3cec8aef7cedd67014ac1.png?size=128")

        await logging_channel.send(embed=embed)



    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        if not await self.is_role_persist_enabled(guild):
            return

        roles_to_give = await self.api.get_stored_roles(guild, member)

        await member.edit(roles=roles_to_give, reason="Roles restore")
        await self.log_role_persist(guild, member, roles_to_give)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        if not await self.is_role_persist_enabled(guild):
            return
        self.bot.logger.debug(f"User {member} left, saving {len(member.roles)} roles")
        await self.api.save_roles(guild, member, member.roles)


def setup(bot: 'GetBeaned'):
    bot.add_cog(RolePersist(bot))
