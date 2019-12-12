# What is GetBeaned (DiscordBot)
It's the bot part of the GetBeaned project, a system to detect and ban spammers, raiders and other annoyances from discord servers.
More than a simple moderation bot, GetBeaned of course offer notes, warns, kicks, mutes, softbans and bans, but is also equiped with a very powerful AutoModerator that detect spammers in real time.

With less false positives than most AutoModerators, GetBeaned won't mute you just for saying "shit". Entirely configurable using a beautiful WebInterface

For more information, feel free to visit the website @ https://getbeaned.me/
You may also want to join our Support Server @ https://discord.gg/rB8eZNs

## Technical Notes

The GetBeaned infrastructure is separated in two parts:

- The Discord bot, that lives here
- The Website, that display the different mod actions taken, and feature an API for the bot to store and retreive information. See https://github.com/getbeaned/GetBeaned-WebInterface for more details, and the code

Please, feel free to read the code, comment, ask, and create issues and pull requests. Improving the bot will make discord a safer place for everyone.
If you do submit a pull request, please use descriptive commit messages, using emojis as described [here](https://gitmoji.carloscuesta.me/)

## Self-hosting
> Please **do not** self-host this bot if you don't know how to secure and manage a server, a database, websites and discord bots. You can use the hosted version, for free, by using the official invite @ https://discordapp.com/oauth2/authorize?client_id=492797767916191745&permissions=1878392007&scope=bot
> If you do self-host, please respect the authors and give credit where it's due. **Do not claim the bot is yours, and follow informations of rules set in the license file**

The bot code is available here for demonstrations and audit purposes. You can however self-host the bot, but, as noted above, only limited support will be available to you. In any case, if you self-host the bot or copy/remix the code, please follow the license file and drop Eyesofcreeper#0001 a PM on discord (Support server https://discord.gg/rB8eZNs)

To self host the bot, you'll need to install the WebSite **first** (this includes nginx, guinicorn, services, django & postgreSQL). More info on the website repository
Once the website is correctly installed and reachable, generate an API key from the website admin panel, then add it into the `credentials.json` file. Also, add in there your discord bot token, and run the bot using a recent version of python (3.6+ at this time)

Have fun!
