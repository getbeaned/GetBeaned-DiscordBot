import datetime

import discord
import re

from discord.ext import commands


from cogs.helpers.helpful_classes import LikeUser
from cogs.helpers.actions import full_process, unban, note, warn, kick, softban, ban


class AutoInspect(commands.Cog):
    """
    Identifies and act on people joining servers.
    """

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.checks = {'autoinspect_pornspam_bots': self.pornspam_bots_check}

    async def pornspam_bots_check(self, member) -> bool:
        # https://regex101.com/r/IeIqbl/1
        result = bool(re.match(r"([A-Z][a-z]+[0-9]{1,4}|[A-Z][a-z]+\.([a-z]+\.[a-z]+|[a-z]+[0-9]{1,2}))", member.name))
        result = result and (member.created_at > datetime.datetime.now() - datetime.timedelta(days=7))

        return result

    async def check_and_act(self, check, name, context) -> bool:
        """
        This returns true if the search should continue, else False.
        """
        action = await self.bot.settings.get(context["guild"], name)

        if action == 1:
            return True

        check_result = await check(context["member"])

        if check_result:
            autoinspect_user = LikeUser(did=4, name="AutoInspector", guild=context["guild"])
            # await full_process(self.bot, note, context["member"], autoinspect_user, reason=f"Automatic note by AutoInspect {name}, following a positive check.")

            embed = discord.Embed()

            embed.colour = discord.colour.Color.red()

            embed.title = f"AutoInspect | Positive Result"
            embed.description = f"{context['member'].name}#{context['member'].discriminator} ({context['member'].id}) AutoInspect check was positive for check {name}"

            embed.set_author(name=self.bot.user.name)
            embed.add_field(name="Member ID", value=context['member'].id)
            embed.add_field(name="Check name", value=name)

            await context["logging_channel"].send(embed=embed)

            if action == 3:
                await full_process(self.bot, softban, context["member"], autoinspect_user, reason=f"Automatic softban by AutoInspect {name}")
                return False
            elif action == 4:
                await full_process(self.bot, ban, context["member"], autoinspect_user, reason=f"Automatic ban by AutoInspect {name}")
                return False

        return True

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()

        if not await self.bot.settings.get(member.guild, 'autoinspect_enable'):
            return 'AutoInspect disabled on this guild.'

        logging_channel = await self.bot.get_cog('Logging').get_logging_channel(member.guild, "logs_autoinspect_channel_id")

        if not logging_channel:
            return 'No logging channel configured for AutoInspect.'

        context = {
            'logging_channel': logging_channel,
            'member': member,
            'guild': member.guild,
        }

        for check_name, check_callable in self.checks.items():
            if not await self.check_and_act(check_callable, check_name, context):
                return True


def setup(bot):
    bot.add_cog(AutoInspect(bot))
