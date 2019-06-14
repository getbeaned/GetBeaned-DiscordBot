import collections
import datetime
import logging
import re
import time
from typing import Union

import discord
import numpy
from discord.ext import commands

from cogs.helpers import checks, context
from cogs.helpers.helpful_classes import LikeUser
from cogs.helpers.actions import full_process, unban, note, warn, kick, softban, ban

from cogs.helpers.level import get_level
from cogs.helpers.triggers import SexDatingDiscordBots, InstantEssayDiscordBots, SexBots
import unicodedata

ZALGO_CHAR_CATEGORIES = ['Mn', 'Me']
DEBUG = False
BAD_WORDS = ['nigga', 'fuck', 'cunt', 'dick', 'cock', 'sex',
             'nigger']

TRIGGERS_ENABLED = [SexDatingDiscordBots, InstantEssayDiscordBots, SexBots]


class CheckMessage:
    def __init__(self, bot, message: discord.Message):
        self.bot = bot
        self.message = message
        self.multiplicator = 1
        self.score = 0

        self.old_multiplicator = self.multiplicator
        self.old_score = self.score

        self.logs = []

        self.invites = []

        self.debug(f"MESSAGE : {message.content:.100} (on #{message.channel.name})")

    @property
    def total(self):
        return round(self.multiplicator * self.score, 3)

    @property
    def old_total(self):
        return round(self.old_multiplicator * self.old_score, 3)

    @property
    def invites_code(self):
        return [i.code for i in self.invites]

    @property
    def logs_for_discord(self):
        return "```\n" + "\n".join(self.logs) + "\n```"

    def debug(self, s):
        fs = f"[s={self.score:+.2f} ({self.score - self.old_score:+.2f})," \
                 f" m={self.multiplicator:+.2f} ({self.multiplicator - self.old_multiplicator:+.2f})," \
                 f" t={self.total:+.2f} ({self.total - self.old_total:+.2f})] > " + s

        if DEBUG:
            if self.message.channel:
                cname = self.message.channel.name
            else:
                cname = "PRIVATE_MESSAGE"

            extra = {"channelname": f"#{cname}", "userid": f"{self.message.author.id}",
                     "username": f"{self.message.author.name}#{self.message.author.discriminator}"}
            logger = logging.LoggerAdapter(self.bot.base_logger, extra)
            logger.debug(f"AM " + fs)

        self.logs.append(fs)
        self.old_score = self.score
        self.old_multiplicator = self.multiplicator


class AutoMod(commands.Cog):
    """
    Custom on_message parser to detect and prevent things like spam, AThere/everyone mentions...
    """

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.invites_regex = re.compile(
            r'discord(?:app\.com|\.gg)[\/invite\/]?(?:(?!.*[Ii10OolL]).[a-zA-Z0-9]{5,6}|[a-zA-Z0-9\-]{2,32})')
        self.message_history = collections.defaultdict(
            lambda: collections.deque(maxlen=7))  # Member -> collections.deque(maxlen=7)

        self.invites_codes_cache = bot.cache.get_cache("automod_invites_codes", expire_after=3600)

        self.automod_cache = bot.cache.get_cache("automod_logs", expire_after=3600)

    async def contains_zalgo(self, message):
        THRESHOLD = 0.5
        if len(message) == 0:
            return False, 0
        word_scores = []
        for word in message.split():
            cats = [unicodedata.category(c) for c in word]
            score = sum([cats.count(banned) for banned in ZALGO_CHAR_CATEGORIES]) / len(word)
            word_scores.append(score)
        total_score = numpy.percentile(word_scores, 75)
        contain = total_score > THRESHOLD
        return contain, total_score

    async def get_invites(self, message: str):

        invites = self.invites_regex.findall(message)

        return list(set(invites)) or None

    async def get_invites_count(self, check_message: CheckMessage):
        message_str = check_message.message.content
        invites = await self.get_invites(message_str)

        if invites is None:
            return 0
        else:
            total = 0
            for invite in invites:
                check_message.debug(f"Checking invite code : {invite}")
                invite_obj = self.invites_codes_cache.get(invite, None)
                try:
                    if invite_obj is None:
                        invite_obj = await self.bot.fetch_invite(invite, with_counts=True)
                    self.invites_codes_cache[invite] = invite_obj
                    if invite_obj.guild.id not in [195260081036591104, 449663867841413120, 512328935304855555] + [check_message.message.guild.id]:
                        minimal_membercount = await self.bot.settings.get(check_message.message.guild, 'automod_minimal_membercount_trust_server')

                        try:
                            member_count = invite_obj.approximate_member_count
                        except AttributeError:
                            member_count = 0
                        if 0 < minimal_membercount < member_count:
                            check_message.debug(
                                f">> Detected invite code for untrusted server but known enough not to act on it (approx. members count: {member_count}): "
                                f"{invite_obj.code} (server : {invite_obj.guild.name} - {invite_obj.guild.id})")
                        else:
                            check_message.debug(
                                f">> Detected invite code for untrusted server (approx. members count: {member_count}): "
                                f"{invite_obj.code} (server : {invite_obj.guild.name} - {invite_obj.guild.id})")

                            check_message.invites.append(invite_obj)
                            total += 1
                    else:
                        check_message.debug(f">> Detected invite code for trusted server:"
                                            f"{invite_obj.code}")
                except discord.errors.NotFound:
                    self.invites_codes_cache[invite] = None
                    check_message.debug(f">> Invalid invite code")

                    continue

            return total

    @commands.command()
    @commands.guild_only()
    @checks.bot_have_minimal_permissions()
    # @checks.have_required_level(8)
    async def automod_debug(self, ctx, *, message_str):
        ctx.message.content = message_str
        cm = await self.check_message(ctx.message, act=False)
        if isinstance(cm, CheckMessage):
            await ctx.send_to(cm.logs_for_discord)
        else:
            await ctx.send_to(f"Automod is disabled or something else. (cm={cm})")

    @commands.command()
    # @checks.have_required_level(8)
    async def automod_logs(self, ctx, message_id: int):
        log = self.automod_cache.get(message_id, ("No logs found for this message ID, maybe it was purged ?", 0))

        await ctx.send_to(log[0])

    async def check_message(self, message, act=True) -> Union[CheckMessage, str]:
        await self.bot.wait_until_ready()
        author = message.author

        if author.bot:
            return "You are a bot"  # ignore messages from other bots

        if message.guild is None:
            return "Not in a guild"  # ignore messages from PMs

        if not await self.bot.settings.get(message.guild, 'automod_enable') and not "[getbeaned:enable_automod]" in str(message.channel.topic):
            return "Automod disabled here"

        if "[getbeaned:disable_automod]" in str(message.channel.topic):
            return "`[getbeaned:disable_automod]` in topic, Automod Disabled here"

        current_permissions = message.guild.me.permissions_in(message.channel)
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
            change_nickname=True
        )

        cond = current_permissions >= wanted_permissions

        if not cond:
            return "No permissions to act"

        check_message = CheckMessage(self.bot, message)
        ctx = await self.bot.get_context(message, cls=context.CustomContext)

        author_level = await get_level(ctx, check_message.message.author)
        automod_ignore_level = await self.bot.settings.get(message.guild, 'automod_ignore_level')

        if author_level >= automod_ignore_level and act:
            return "Author level is too high, I'm not going further"

        if author.status is discord.Status.offline:
            check_message.multiplicator += await self.bot.settings.get(message.guild, 'automod_multiplictor_offline')
            check_message.debug("Author is offline (probably invisible)")

        if author.created_at > datetime.datetime.now() - datetime.timedelta(days=7):
            check_message.multiplicator += await self.bot.settings.get(message.guild, 'automod_multiplictor_new_account')
            check_message.debug("Author account is less than a week old")

        if author.joined_at > datetime.datetime.now() - datetime.timedelta(days=1):
            check_message.multiplicator += await self.bot.settings.get(message.guild, 'automod_multiplictor_just_joined')
            check_message.debug("Author account joined less than a day ago")

        if author.is_avatar_animated():
            check_message.multiplicator += await self.bot.settings.get(message.guild, 'automod_multiplictor_have_nitro')
            check_message.debug("Author account is nitro'd (or at least I can detect an animated avatar)")

        if len(author.roles) > 2:  # Role duckies is given by default
            check_message.multiplicator += await self.bot.settings.get(message.guild, 'automod_multiplictor_have_roles')
            check_message.debug("Author account have a role in the server")

        if author_level == 0:
            check_message.multiplicator += await self.bot.settings.get(message.guild, 'automod_multiplictor_bot_banned')
            check_message.debug("Author is bot-banned")

        if check_message.multiplicator <= 0:
            check_message.debug("Multiplicator is <= 0, exiting without getting score")
            return check_message  # Multiplicator too low!

        check_message.debug("Multiplicator calculation done")

        ## Multiplicator calculation done!

        total_letters = len(message.content)
        total_captial_letters = sum(1 for c in message.content if c.isupper())
        # If no letters, then 100% caps.
        caps_percentage = total_captial_letters / total_letters if total_letters > 0 else 1

        if caps_percentage >= 0.7 and total_letters > 10:
            check_message.score += await self.bot.settings.get(message.guild, 'automod_score_caps')
            check_message.debug(f"Message is written in CAPS LOCK (% of caps: {round(caps_percentage * 100, 3)} —"
                                f" total length: {total_letters})")

        # if len(message.embeds) >= 1 and any([e.type == "rich" for e in message.embeds]):
        #   check_message.score += await self.bot.settings.get(message.guild, 'automod_score_embed')
        #   check_message.debug(f"Message from a USER contain an EMBED !? (Used to circumvent content blocking)")

        if "@everyone" in message.content and not message.mention_everyone:
            check_message.score += await self.bot.settings.get(message.guild, 'automod_score_everyone')
            check_message.debug(
                f"Message contains an ATeveryone that discord did not register as a ping (failed attempt)")

        mentions = set(message.mentions)
        if len(mentions) > 3:
            check_message.score += await self.bot.settings.get(message.guild, 'automod_score_too_many_mentions')
            m_list = [a.name + '#' + a.discriminator for a in mentions]
            check_message.debug(f"Message mentions more than 3 people ({m_list})")

        if await self.get_invites_count(check_message) >= 1 and str(message.channel.id) not in str(
                await self.bot.settings.get(message.guild, 'automod_ignore_invites_in')):  # They can add multiple channels separated by a " "
            check_message.score += await self.bot.settings.get(message.guild, 'automod_score_contain_invites')
            check_message.debug(f"Message contains invite(s) ({check_message.invites_code})")

        if message.content and "[getbeaned:disable_spam_detection]" not in str(message.channel.topic):
            # TODO: Check images repeat
            repeat = self.message_history[check_message.message.author].count(check_message.message.content)
            if repeat >= 3:
                check_message.score += await self.bot.settings.get(message.guild, 'automod_score_repeated') * repeat
                check_message.debug(f"Message was repeated by the author {repeat} times")

        bad_words_in_message = {b_word for b_word in BAD_WORDS if b_word in check_message.message.content.lower()}
        bad_words_count = len(bad_words_in_message)

        if bad_words_count >= 1:
            check_message.score += await self.bot.settings.get(message.guild, 'automod_score_bad_words') * bad_words_count
            check_message.debug(f"Message contains {bad_words_count} bad words ({', '.join(bad_words_in_message)})")

        if not check_message.message.content.lower().startswith(("dh", "!", "?", "§", "t!", ">", "<", "-", "+")) or len(
                check_message.message.content) > 30 \
                and check_message.message.content.lower() not in ['yes', 'no', 'maybe', 'hey', 'hi', 'hello', 'oui',
                                                                  'non', 'bonjour', '\o', 'o/', ':)', ':D', ':(', 'ok',
                                                                  'this', 'that', 'yup'] \
                and act:
            # Not a command or something
            self.message_history[check_message.message.author].append(
                check_message.message.content)  # Add content for repeat-check later.

        contains_zalgo, zalgo_score = await self.contains_zalgo(message.content)

        if contains_zalgo:
            check_message.score += await self.bot.settings.get(message.guild, 'automod_score_zalgo')
            check_message.debug(f"Message contains zalgo (zalgo_score={zalgo_score})")

        if await self.bot.settings.get(message.guild, 'autotrigger_enable'):
            check_message.debug("Running AutoTrigger checks")
            instancied_triggers = [t(check_message) for t in TRIGGERS_ENABLED]

            for trigger in instancied_triggers:
                score = await trigger.run()
                if score != 0:
                    check_message.score += score

        check_message.debug("Score calculation done")
        check_message.debug(f"Total for message is {check_message.total}, applying actions if any")

        automod_user = LikeUser(did=1, name="AutoModerator", guild=message.guild)

        # Do we need to delete the message ?
        automod_delete_message_score = await self.bot.settings.get(message.guild, 'automod_delete_message_score')
        if check_message.total >= automod_delete_message_score > 0:
            check_message.debug(f"Deleting message because score "
                                f"**{check_message.total}** >= {automod_delete_message_score}")
            try:
                if act:
                    await message.delete()
                    if await self.bot.settings.get(message.guild, 'automod_note_message_deletions'):
                        await full_process(ctx.bot, note, message.author, automod_user, reason="Automod deleted a message from this user.",
                                           automod_logs="\n".join(check_message.logs))

            except discord.errors.NotFound:
                check_message.debug(f"Message already deleted!")

        else:  # Too low to do anything else
            return check_message

        # That's moderation acts, where the bot grabs his BIG HAMMER and throw it in the user face
        # Warning
        automod_warn_score = await self.bot.settings.get(message.guild, 'automod_warn_score')
        automod_kick_score = await self.bot.settings.get(message.guild, 'automod_kick_score')
        automod_softban_score = await self.bot.settings.get(message.guild, 'automod_softban_score')
        automod_ban_score = await self.bot.settings.get(message.guild, 'automod_ban_score')

        # Lets go in descending order:
        if check_message.total >= automod_ban_score > 0:
            check_message.debug(f"Banning user because score **{check_message.total}** >= {automod_ban_score}")
            if act:
                r = f"Automatic action from automod. " \
                    f"Banning user because score **{check_message.total}** >= {automod_ban_score}"
                await full_process(ctx.bot, ban, message.author, automod_user,
                                   reason=r,
                                   automod_logs="\n".join(check_message.logs))

        elif check_message.total >= automod_softban_score > 0:
            check_message.debug(f"SoftBanning user because score **{check_message.total}** >= {automod_softban_score}")
            if act:
                r = f"Automatic action from automod. " \
                    f"SoftBanning user because score **{check_message.total}** >= {automod_softban_score}"
                await full_process(ctx.bot, softban, message.author, automod_user,
                                   reason=r,
                                   automod_logs="\n".join(check_message.logs))

        elif check_message.total >= automod_kick_score > 0:
            check_message.debug(f"Kicking user because score **{check_message.total}** >= {automod_kick_score}")
            if act:
                r = f"Automatic action from automod. " \
                    f"Kicking user because score **{check_message.total}** >= {automod_kick_score}"
                await full_process(ctx.bot, kick, message.author, automod_user,
                                   reason=r,
                                   automod_logs="\n".join(check_message.logs))
        elif check_message.total >= automod_warn_score > 0:
            check_message.debug(f"Warning user because score **{check_message.total}** >= {automod_warn_score}")
            if act:
                r = f"Automatic action from automod. " \
                    f"Warning user because score **{check_message.total}** >= {automod_warn_score}"
                await full_process(ctx.bot, warn, message.author, automod_user,
                                   reason=r,
                                   automod_logs="\n".join(check_message.logs))

        ctx.logger.info("Automod acted on a message, logs follow.")
        ctx.logger.info("\n".join(check_message.logs))
        return check_message

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if not message.guild:
            return False  # No PMs

        ret = await self.check_message(message)

        try:
            logs = ret.logs_for_discord
        except AttributeError:
            logs = str(ret)

        self.automod_cache[message.id] = (logs, int(time.time()))

    @commands.Cog.listener()
    async def on_message_edit(self, _, message):
        await self.bot.wait_until_ready()
        if not len(message.content): return
        ret = await self.check_message(message)

        try:
            logs = ret.logs_for_discord
        except AttributeError:
            logs = str(ret)

        logs = self.automod_cache.get(message.id, ("(No logs stored before the edit)", 0))[0] + "\n==AN EDIT WAS MADE==\n" + logs

        self.automod_cache[message.id] = (logs, int(time.time()))



def setup(bot):
    bot.add_cog(AutoMod(bot))
