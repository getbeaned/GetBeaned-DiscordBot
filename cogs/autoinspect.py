import datetime
import re
import typing

import discord
from discord.ext import commands

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from cogs.helpers.helpful_classes import LikeUser
from cogs.helpers.actions import full_process, softban, ban


class AutoInspect(commands.Cog):
    """
    Identifies and act on people joining servers.
    """

    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.api = bot.api
        self.checks = {'autoinspect_pornspam_bots': self.pornspam_bots_check,
                       'autoinspect_username_check': self.username_check}
        self.bypass_cache = bot.cache.get_cache("autoinspect_bypass_cache", expire_after=600, strict=True)

    async def username_check(self, member: discord.Member) -> bool:
        string = member.name
        matches = await self.bot.settings.get_bad_word_matches(member.guild, string)
        return bool(len(matches))

    async def pornspam_bots_check(self, member: discord.Member) -> bool:
        # https://regex101.com/r/IeIqbl/1

        first_version_result = bool(re.match(r"^([A-Z][a-z]+[0-9]{1,4}|[A-Z][a-z]+\.([a-z]+\.[a-z]+|[a-z]+[0-9]{1,2}))$", member.name))
        first_version_result = first_version_result \
                               and (member.created_at > datetime.datetime.now() - datetime.timedelta(days=14))

        # https://regex101.com/r/ns1L0E/2
        second_version_result = bool(re.match(r"^[A-Z][a-z]{2,10}[0-9]{1,3}[a-z0-9]{1,3}$", member.name))
        second_version_result = second_version_result \
                                and (member.created_at > datetime.datetime.now() - datetime.timedelta(days=7)) \
                                and member.avatar_url == member.default_avatar_url

        return first_version_result or second_version_result

    async def check_and_act(self, check: typing.Callable[[discord.Member], typing.Awaitable], name: str, context: dict) -> bool:
        """
        This returns true if the search should continue, else False.
        """
        action = await self.bot.settings.get(context["guild"], name)

        if action == 1:
            return True

        check_result = await check(context["member"])

        if check_result:

            if await self.bot.settings.get(context['guild'], 'autoinspect_bypass_enable'):
                logs = f"To prevent False Positives, AutoInspect added a mark on this account for 600 seconds. " \
                    f"If the user {context['member'].name}#{context['member'].discriminator} tries to rejoin the server in the " \
                    f"next 10 minutes, AutoInspect rules will not apply on him."
            else:
                logs = "As requested by the server settings, no exceptions are allowed on AutoInspect."

            autoinspect_user = LikeUser(did=4, name="AutoInspector", guild=context["guild"])
            # await full_process(self.bot, note, context["member"], autoinspect_user, reason=f"Automatic note by AutoInspect {name}, following a positive check.")

            embed = discord.Embed()

            embed.colour = discord.colour.Color.red()

            embed.title = f"AutoInspect | Positive Result"
            embed.description = f"{context['member'].name}#{context['member'].discriminator} ({context['member'].id}) AutoInspect check was positive for check {name}"

            embed.set_author(name=self.bot.user.name)
            embed.add_field(name="Member ID", value=context['member'].id)
            embed.add_field(name="Check name", value=name)
            embed.add_field(name="Info", value=logs, inline=False)

            await context["logging_channel"].send(embed=embed)

            if action == 3:
                await full_process(self.bot, softban, context["member"], autoinspect_user, reason=f"Automatic softban by AutoInspect {name}", automod_logs=logs)
                return False
            elif action == 4:
                await full_process(self.bot, ban, context["member"], autoinspect_user, reason=f"Automatic ban by AutoInspect {name}", automod_logs=logs)
                return False

        return True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.bot.wait_until_ready()

        if not await self.bot.settings.get(member.guild, 'autoinspect_enable'):
            return 'AutoInspect disabled on this guild.'

        logging_channel = await self.bot.get_cog('Logging').get_logging_channel(member.guild, "logs_autoinspect_channel_id")

        if not logging_channel:
            return 'No logging channel configured for AutoInspect.'

        if member in self.bypass_cache.get(member.guild, []) and await self.bot.settings.get(member.guild, 'autoinspect_bypass_enable'):
            return "User was already AutoInspected previously, don't do that again."

        self.bypass_cache[member.guild] = self.bypass_cache.get(member.guild, []) + [member]

        context = {
            'logging_channel': logging_channel,
            'member': member,
            'guild': member.guild,
        }

        for check_name, check_callable in self.checks.items():
            if not await self.check_and_act(check_callable, check_name, context):
                return True


def setup(bot: 'GetBeaned'):
    bot.add_cog(AutoInspect(bot))
