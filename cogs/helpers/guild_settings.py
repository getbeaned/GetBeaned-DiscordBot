import re
import typing

import discord

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned


class Settings:
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.settings_cache = bot.cache.get_cache("settings", expire_after=900, strict=True)
        self.vip_bad_regex_cache = bot.cache.get_cache("vip_bad_regex", expire_after=1200, strict=False)

    async def add_to_cache(self, guild: discord.Guild, settings: dict):
        self.settings_cache[guild] = settings

    async def get(self, guild: discord.Guild, setting: str):
        await self.bot.wait_until_ready()

        gs = self.settings_cache[guild]

        if gs:  # Use cache
            return gs[setting]
        else:
            # Get from internet
            gs = await self.bot.api.get_settings(guild)
            await self.add_to_cache(guild, gs)
            return gs[setting]

    async def set(self, guild: discord.Guild, setting: str, value):
        await self.bot.wait_until_ready()
        try:
            del self.settings_cache[guild]
        except KeyError:
            pass

        await self.bot.api.set_settings(guild, setting, value)

    async def get_bad_word_matches(self, guild: discord.Guild, string: str) -> typing.Iterable[typing.Tuple[str, str]]:
        bad_regex_list = []

        if not await self.get(guild, "vip"):
            bad_words_list = ['nigga', 'fuck', 'cunt', 'dick', 'cock', 'sex', 'nigger']
            for word in bad_words_list:
                bad_regex_list.append(re.compile(f"\\b{word}\\b(?i)(?m)"))
        else:
            bad_regex_list = self.vip_bad_regex_cache[guild]

            if bad_regex_list is None:
                bad_regex_list = []
                words = await self.get(guild, "vip_custom_bad_words_list")
                bad_words_list = str(words).splitlines(keepends=False)
                regexes = [f"\\b{word}\\b(?i)(?m)" for word in bad_words_list]

                regexes_str = await self.get(guild, "vip_custom_bad_regex_list")
                regexes = regexes + str(regexes_str).splitlines(keepends=False)

                for regex in regexes:
                    try:
                        bad_regex_list.append(re.compile(regex))
                    except Exception as e:
                        self.bot.logger.debug(f"{regex} -> {e}")

                self.vip_bad_regex_cache[guild] = bad_regex_list

        matches = []
        for regex in bad_regex_list:
            match = regex.search(string)
            if match:
                matches.append((match.string, regex.pattern))

        return matches
