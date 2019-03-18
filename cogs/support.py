import discord
from discord.ext import commands

from cogs.helpers import checks
from cogs.helpers.level import get_level


class Support(commands.Cog):
    """Cog for various support commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild is None:
            return

        if message.author is self.bot.user:
            return

        pm_channel = self.bot.get_channel(557294214417874945)

        await pm_channel.send(f"{message.author.mention} ({message.author.name}#{message.author.discriminator})\n```{message.content[:1900]}```")

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(1)
    async def level(self, ctx, user: discord.Member = None):
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

    @commands.command(aliases=["permissions_check", "permission_check"])
    @commands.guild_only()
    @checks.have_required_level(1)
    async def bot_permissions_check(self, ctx):
        current_permissions:discord.Permissions = ctx.message.guild.me.permissions_in(ctx.channel)

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

def setup(bot):
    bot.add_cog(Support(bot))
