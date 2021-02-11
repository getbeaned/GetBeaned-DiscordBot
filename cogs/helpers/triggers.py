"""
This file is meant to keep code for AutoTriggers, so that the automod file isn't too big
Everything here should be imported by automod if enabled
"""
import datetime
import re
import sys
import traceback
import typing
from typing import List

import discord
import ftfy

if typing.TYPE_CHECKING:
    from cogs.automod import CheckMessage


class AutoTrigger:
    def __init__(self, message: 'CheckMessage'):
        self.check_message = message
        self.message = message.message
        self.autotrigger_name = "Generic AutoTrigger"
        self.autotrigger_dbname = "generic"

    async def is_enabled(self) -> bool:
        pref_name = f"autotrigger_{self.autotrigger_dbname}_score"

        return (await self.check_message.bot.settings.get(self.message.guild, pref_name)) != 0

    async def get_score(self) -> float:
        pref_name = f"autotrigger_{self.autotrigger_dbname}_score"

        return await self.check_message.bot.settings.get(self.message.guild, pref_name)

    async def check(self) -> bool:
        return False

    async def run(self) -> float:
        if await self.is_enabled():
            try:
                ret = await self.check()
            except AssertionError:
                ret = False
                #_, _, tb = sys.exc_info()
                # traceback.print_tb(tb)  # Fixed format
                #tb_info = traceback.extract_tb(tb)
                #filename, line, func, text = tb_info[-1]

                #shown_text = text.replace("assert await ", "").replace("assert ", "")

                #self.check_message.debug('The trigger failed on line {} (stmt is `{}`)'.format(line, shown_text))

            self.check_message.debug(f"> Check ran {self.autotrigger_name} with result {ret}")
            if ret:
                score = await self.get_score()
                self.check_message.debug(f"> > {self.autotrigger_name}: adding {score} points to score")
                return score
            else:
                return 0
        else:
            return 0


class BadStrings(AutoTrigger):
    def __init__(self, message):
        super().__init__(message)
        self.autotrigger_name = "Bad Strings"
        self.autotrigger_dbname = "badstrings"

    async def check(self):
        # There are a tons of characters in there
        assert await message_contains_any(self.message,
                                          ["بٍٍٍٍََُُُِّّّْرٍٍٍٍََُُِِّّّْآٍٍٍَُّ🇮🇹 بٍٍٍٍََُُُِّّّْرٍٍٍٍََُُِِّّّْآٍٍٍَُّ🇮🇹",
                                           "بٍٍٍٍََُُُِّّّْرٍٍٍٍََُُِِّّّْآٍٍٍَُّ🇮🇹 بٍٍٍٍََُُُِّّّْرٍٍٍٍََُُِِّّّْآٍٍٍَُّ🇮🇹",
                                           "بٍٍٍٍََُُُِّّّْرٍٍٍٍََُُِِّّّْآٍٍٍَُّ",
                                           "بٍٍٍرٍٍٍآٍٍٍ"])
        return True


class LibraCryptoDiscordBots(AutoTrigger):
    def __init__(self, message):
        super().__init__(message)
        self.autotrigger_name = "Libra Discord Bots"
        self.autotrigger_dbname = "libradiscordbots"

    async def check(self):
        # Notice the weird i
        assert await message_contains_x_of(self.message, 2,
                                          ["christmas airdrop",
                                           "airdrop",
                                           "air drop",
                                           "airdrop",
                                           "air drop",
                                           "https://etherairdrop.io/",
                                           "worked for me so its legit",
                                           "Ethereum 2.0 Airdrop",
                                           "heres the official tweet",
                                           "dont miss the current 1INCH",
                                           "okey that im sharing this but i claimed 1200$",
                                           "i got 1400 dollars worth of 1inch tokens",
                                           "1inch",
                                           "1inch-airdrop.net",
                                           "etherаirdrop.net",
                                           "ethereum аirdrop",
                                           "ethereum-airdrop.io"], normalize=True)

        assert await member_joined_x_days_ago(self.message.author, x=2)
        return True


class DMMeNudesDiscordBots(AutoTrigger):
    def __init__(self, message):
        super().__init__(message)
        self.autotrigger_name = "Nudes Selling Discord Bots"
        self.autotrigger_dbname = "sexdatingdiscordbots"

    async def check(self):
        assert await message_contains_any(self.message, ["Dm me guys if you want to see my nudes for free", "Dm me guys if you want to see my nudes for  free"])
        assert await member_joined_x_hours_ago(self.message.author, x=1)
        return True


class SexDatingDiscordBots(AutoTrigger):
    def __init__(self, message):
        super().__init__(message)
        self.autotrigger_name = "Sex Dating Discord Bots"
        self.autotrigger_dbname = "sexdatingdiscordbots"

    async def check(self):
        assert await message_contains_any(self.message, ["discord.amazingsexdating.com", "Sex dating discord >", "Sex Dating >", "Best casino online >", "adultheroesofhentai.cf", "one of the best hentai games - free for adults now!"])
        assert await user_dont_have_a_profile_picture(self.message.author)
        assert await member_joined_x_days_ago(self.message.author, x=1)
        return True


# http://write-me-tender.ml/ - Instant Essay Writing Service! Best Prices - Best Writers !
# http://cool-essay.ga - Order essay writing online! Smarter and faster than your profs!
# http://write-some.ga/ - From admission essays to graduate dissertations - rely on a trusted service to do it for you!
class InstantEssayDiscordBots(AutoTrigger):
    def __init__(self, message):
        super().__init__(message)
        self.autotrigger_name = "Instant Essay Discord Bots"
        self.autotrigger_dbname = "instantessaydiscordbots"

    async def check(self):
        assert await message_contains_x_of(self.message, 4, ["write-me-tender.ml", "cool-essay.ga", "essay", "writers", "profs", "order essay", "instant essay",
                                                             "Instant Essay Writing Service!", "Order essay writing online!", "Best Prices - Best Writers !", "write-some.ga",
                                                             "admission essays", "graduate dissertations"])

        assert await member_joined_x_days_ago(self.message.author, x=1)
        assert await user_created_x_days_ago(self.message.author, x=3)
        assert not await user_have_nitro(self.message.author)

        return True


# :heart_eyes: 🥰 My 18+ photos :stuck_out_tongue_winking_eye: - https://www.nakedphotos.club/
class SexBots(AutoTrigger):
    def __init__(self, message):
        super().__init__(message)
        self.autotrigger_name = "Sex Bots"
        self.autotrigger_dbname = "sexbots"

    async def check(self):
        assert await message_contains_x_of(self.message, 1, ["privatepage.vip", "nakedphotos.club", "viewc.site", "My naked photos", "My 18+ photos", "Awesome Gift of the Day",
                                                             "https://bit.ly/KittyKiss"])

        assert await member_joined_x_days_ago(self.message.author, x=2)

        # If the account is not that old or if it's matching the name pattern.
        assert (await user_created_x_days_ago(self.message.author, x=14) or
                bool(re.match(r"([A-Z][a-z]+[0-9]{1,4}|[A-Z][a-z]+\.([a-z]+\.[a-z]+|[a-z]+[0-9]{1,2}))$", self.message.author.name)))

        assert not await user_have_nitro(self.message.author)

        return True


async def user_dont_have_a_profile_picture(user: discord.User) -> bool:
    return user.avatar_url == user.default_avatar_url


async def user_have_nitro(user: discord.User) -> bool:
    return user.is_avatar_animated()


async def member_joined_x_days_ago(member: discord.Member, x=1) -> bool:
    return member.joined_at > datetime.datetime.now() - datetime.timedelta(days=x)

async def member_joined_x_hours_ago(member: discord.Member, x=1) -> bool:
    return member.joined_at > datetime.datetime.now() - datetime.timedelta(days=x)

async def user_created_x_days_ago(member: discord.Member, x=1) -> bool:
    return member.created_at > datetime.datetime.now() - datetime.timedelta(hours=x)

async def message_contains_any(message: discord.Message, texts: List[str], normalize=False) -> bool:
    return await message_contains_x_of(message, 1, texts, normalize)

async def message_contains_x_of(message: discord.Message, x: int, texts: List[str], normalize=False) -> bool:
    assert x <= len(texts)
    assert x > 0

    if normalize:
        content = ftfy.fix_text(message.content, normalization='NFKC').lower().strip()
    else:
        content = message.content.lower().strip()

    current_count = 0
    for text in texts:
        if text.lower() in content:
            current_count += 1
            if current_count >= x:
                return True
    return False
