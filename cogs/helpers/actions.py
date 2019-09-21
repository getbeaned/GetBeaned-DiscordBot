import asyncio
import datetime

import discord
from discord import Color

from cogs.helpers.helpful_classes import LikeUser

colours = {'unban': Color.green(),
           'unmute': Color.dark_green(),
           'note': Color.light_grey(),
           'warn': Color.orange(),
           'mute': Color.dark_purple(),
           'kick': Color.dark_orange(),
           'softban': Color.red(),
           'ban': Color.dark_red()
           }


async def thresholds_enforcer(bot, victim, action_type):
    if not await bot.settings.get(victim.guild, 'thresholds_enable'):
        return False

    reason = "Thresholds enforcing"
    mod_user = LikeUser(did=2, name="ThresholdsEnforcer", guild=victim.guild)

    counters = await bot.api.get_counters(victim.guild, victim)

    if action_type == 'note' or action_type == 'unban':
        return False

    elif action_type == 'warn':
        thresholds_warns_to_kick = await bot.settings.get(victim.guild, 'thresholds_warns_to_kick')
        if thresholds_warns_to_kick and counters['warn'] % thresholds_warns_to_kick == 0:
            logs = f"Total of {counters['warn']}, we want {counters['warn']}%{thresholds_warns_to_kick} = {counters['warn'] % thresholds_warns_to_kick} = 0"
            await full_process(bot, kick, victim, mod_user, reason=reason, automod_logs=logs)

    elif action_type == 'mute':
        thresholds_mutes_to_kick = await bot.settings.get(victim.guild, 'thresholds_mutes_to_kick')
        if thresholds_mutes_to_kick and counters['mute'] % thresholds_mutes_to_kick == 0:
            logs = f"Total of {counters['mute']}, we want {counters['mute']}%{thresholds_mutes_to_kick} = {counters['mute'] % thresholds_mutes_to_kick} = 0"
            await full_process(bot, kick, victim, mod_user, reason=reason, automod_logs=logs)

    elif action_type == 'kick':
        thresholds_kicks_to_bans = await bot.settings.get(victim.guild, 'thresholds_kicks_to_bans')
        if thresholds_kicks_to_bans and counters['kick'] % thresholds_kicks_to_bans == 0:
            logs = f"Total of {counters['kick']}, we want {counters['kick']}%{thresholds_kicks_to_bans} = {counters['kick'] % thresholds_kicks_to_bans} = 0"
            await full_process(bot, ban, victim, mod_user, reason=reason, automod_logs=logs)

    elif action_type == 'softban':
        thresholds_softbans_to_bans = await bot.settings.get(victim.guild, 'thresholds_softbans_to_bans')
        if thresholds_softbans_to_bans and counters['softban'] % thresholds_softbans_to_bans == 0:
            logs = f"Total of {counters['softban']}, we want {counters['softban']}%{thresholds_softbans_to_bans} = {counters['softban'] % thresholds_softbans_to_bans} = 0"
            await full_process(bot, ban, victim, mod_user, reason=reason, automod_logs=logs)
    else:
        return False

    return True


async def ban(victim, reason=None):
    await victim.guild.ban(victim, reason=reason)


async def softban(victim, reason=None):
    await victim.guild.ban(victim, reason=reason)
    await victim.guild.unban(victim, reason=reason)


async def kick(victim, reason=None):
    await victim.guild.kick(victim, reason=reason)


async def mute(victim, reason=None):
    muted_role = discord.utils.get(victim.guild.roles, name="GetBeaned_muted")
    await victim.add_roles(muted_role, reason=reason)

async def unmute(victim, reason=None):
    muted_role = discord.utils.get(victim.guild.roles, name="GetBeaned_muted")
    await victim.remove_roles(muted_role, reason=reason)


async def warn(victim, reason=None):
    pass


async def note(victim, reason=None):
    pass


async def unban(victim, reason=None):
    await victim.guild.unban(victim, reason=reason)


async def get_action_log_embed(bot, case_number, webinterface_url, action_type, victim, moderator, reason=None, attachement_url=None,
                               automod_logs=None):
    embed = discord.Embed()
    if attachement_url:
        embed.set_image(url=attachement_url)

    embed.colour = colours[action_type]
    embed.title = f"{action_type.title()} | Case #{case_number}"
    embed.description = reason

    embed.add_field(name="Responsible Moderator", value=f"{moderator.name}#{moderator.discriminator}", inline=True)
    embed.add_field(name="Victim", value=f"{victim.name}#{victim.discriminator} ({victim.id})", inline=True)
    embed.add_field(name="More info on the webinterface", value=webinterface_url, inline=False)

    if automod_logs:
        embed.add_field(name="Automod logs", value=automod_logs[:1000], inline=False)

    embed.set_author(name=bot.user.name)

    embed.timestamp = datetime.datetime.now()

    return embed


async def full_process(bot, action_coroutine, victim, moderator, reason=None, attachement_url=None, automod_logs=None):
    """
    A little bit of explanation about what's going on there.

    This is the entry point for action-ing on a `victim`. What this function does is first to POST the action to the
    WebInterface API, then give the user the URL the link to the specific action got, and ignore if that part fails.

    We then actually act (ban/kick/what_ever) if needed, and finally check for thresholds enforcement (and this may do
    something else to the user, like kicking/banning him, calling this back).

    Lastly, we try to see if we should log messages to a #mod-log channel, and log if wanted to.
    """

    action_type = action_coroutine.__name__

    res = await bot.api.add_action(guild=victim.guild,
                                   user=victim,
                                   action_type=action_type,
                                   reason=reason,
                                   responsible_moderator=moderator,
                                   attachment=attachement_url,
                                   automod_logs=automod_logs,
                                   )

    url = "https://getbeaned.me" + res['result_url']
    quoted_reason = '> '.join(('> ' + reason).splitlines(True))
    try:
        asyncio.ensure_future(victim.send(f"You have received a {action_type}, with the following reason\n"
                                          f"{quoted_reason}\n\n"
                                          f"For more info, please see {url}, you may have to login with your Discord account. "
                                          f"You can appeal this with the moderator of your choice."))
    except AttributeError:
        # LikeUser dosen't have a send attr
        pass
    await action_coroutine(victim, reason)

    th = await thresholds_enforcer(bot, victim, action_type)

    if await bot.settings.get(victim.guild, 'logs_enable'):
        # Log this to #mod-log or whatever
        # Beware to see if the channel id is actually in the same server (to compare, we will see if the current server
        # owner is the same as the one in the target channel). If yes, even if it's not the same server, we will allow
        # logging there

        channel_id = await bot.settings.get(victim.guild, 'logs_moderation_channel_id')

        if channel_id != 0:
            channel = bot.get_channel(channel_id)

            if not channel:
                bot.logger.warning(f"There is something fishy going on with guild={victim.guild.id}! "
                                   f"Their logs_channel_id={channel_id} can't be found!")
            elif not channel.guild.owner == victim.guild.owner:
                bot.logger.warning(f"There is something fishy going on with guild={victim.guild.id}! "
                                   f"Their logs_channel_id={channel_id} don't belong to them!")
            else:

                case_number = res['case_number']
                if await bot.settings.get(victim.guild, 'logs_as_embed'):
                    embed = await get_action_log_embed(bot,
                                                       case_number,
                                                       url,
                                                       action_type,
                                                       victim,
                                                       moderator,
                                                       reason=reason,
                                                       attachement_url=attachement_url,
                                                       automod_logs=None)

                    # On "ensure future" pour envoyer le message en arriere plan
                    # Comme ca, logger ne limite pas les thresholds aux ratelimits de discord
                    async def send(embed):
                        try:
                            await channel.send(embed=embed)
                        except discord.errors.Forbidden:
                            pass

                    asyncio.ensure_future(send(embed))
                else:
                    textual_log = f"**{action_type}** #{case_number} " \
                        f"on {victim.name}#{victim.discriminator} (`{victim.id}`)\n" \
                        f"**Reason**: {reason}\n" \
                        f"**Moderator**: {moderator.name}#{moderator.discriminator} (`{moderator.id}`)\n" \
                        f"More info at {url} "
                    async def send(log):
                        try:
                            await channel.send(log)
                        except discord.errors.Forbidden:
                            pass

                    asyncio.ensure_future(send(textual_log))

    return {"user_informed": None,
            "url": url,
            "thresholds_enforced": th}
