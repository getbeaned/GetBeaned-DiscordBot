import typing

import discord

if typing.TYPE_CHECKING:
    from cogs.helpers.context import CustomContext

BANNED_MEMBERS_IDS = [
    556456702753636400,  # See https://getbeaned.me/actions/17049
    693482914318385212,  # See https://getbeaned.me/users/693482914318385212 (Gory stabbing videos)
]

OWNERS_IDS = [
    138751484517941259,  # Eyesofcreeper#0001
]

MODERATORS_IDS = [
    344375352220712961,  # ironic toblerone#3525
    183273311503908864,  # OAlpouin#6797
    181846573351829504,  # PierrePV#3537
    135446225565515776,  # Taoshi#0001
    300247046856900629,  # Wolterhon#3938
    251996890369884161,  # Subtleknifewielder#1927
]


# noinspection PyUnreachableCode
async def get_level(ctx: 'CustomContext', user: discord.Member):
    """
    Levels are a permission system so that you can access your level command and below.

    The levels are given by

    | Level | Description               |
    ------------------------------------|
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

    user_id = user.id

    # Level 10
    if user_id in OWNERS_IDS or user_id == ctx.bot.user.id:
        return 10

    # Level 9
    if False:
        return 9

    # Level 8
    if user_id in MODERATORS_IDS:
        return 8

    # Level 7
    if False:
        return 7

    # Level 6
    if False:
        return 6

    # Level 0
    # Special case since even if you own a server, if you are bot-banned, I don't want you to be able to use anything.
    if user_id in BANNED_MEMBERS_IDS:
        return 0

    if not ctx.guild:  # Private messages
        return 1

    # Level 5
    if user.guild.owner == user:
        return 5

    # Level 4
    admins_ids = await ctx.bot.settings.get(user.guild, 'permissions_admins')

    if user.guild_permissions.administrator:
        return 4
    elif user.id in admins_ids:
        return 4
    elif set(admins_ids).intersection(set([r.id for r in user.roles])):
        return 4

    # Level 3
    # We need to be able to add moderators without giving them a discord permission.
    # We are checking permissions here (give a ban permission : members can use
    # the ban, softban commands, a kick permission for the kick, warns and note commands)
    moderators_ids = await ctx.bot.settings.get(user.guild, 'permissions_moderators')

    if user.guild_permissions.ban_members:
        return 3
    elif user.id in moderators_ids:
        return 3
    elif set(moderators_ids).intersection(set([r.id for r in user.roles])):
        return 3

    # Level 2
    # This will basically be half-mods, that can user kick-permission commands, but can't ban or do much damage
    trusted_ids = await ctx.bot.settings.get(user.guild, 'permissions_trusted')

    if user.guild_permissions.kick_members:
        return 2
    elif user.id in trusted_ids:
        return 2
    elif set(trusted_ids).intersection(set([r.id for r in user.roles])):
        return 2

    banned_ids = await ctx.bot.settings.get(user.guild, 'permissions_banned')
    if user.id in banned_ids or set(banned_ids).intersection(set([r.id for r in user.roles])):
        return 0

    # Level 1
    # Rest of the members.
    return 1

    # Level 0 was checked before, so no need to do that again
