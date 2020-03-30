import asyncio
import json

from discord.ext import commands
from trello import TrelloClient

with open("credentials.json", "r") as f:
    credentials = json.load(f)

import typing

if typing.TYPE_CHECKING:
    from cogs.helpers.GetBeaned import GetBeaned

from cogs.helpers.context import CustomContext

TRELLO_KEY = credentials["trello_api_key"]
TRELLO_TOKEN = credentials["trello_api_token"]

trello_client = TrelloClient(
    api_key=TRELLO_KEY,
    api_secret=TRELLO_TOKEN
)


async def wait_for_answer(ctx: 'CustomContext', additional_check: typing.Callable = None):
    if additional_check is None:
        def additional_check(m):
            return True

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    while True:
        try:
            answer = await ctx.bot.wait_for('message', check=check, timeout=600)
        except asyncio.TimeoutError:
            await ctx.message.channel.send("You took too long to answer, operation canceled.")
            return None
        if answer.content.lower() == "exit":
            await ctx.message.channel.send("You canceled the operation.")
            return None
        elif not additional_check(answer):
            await ctx.message.channel.send("Oops, your answer does NOT match what I'm expecting. Please try again or type `exit` to quit.")
        else:
            return answer


class Suggestions(commands.Cog):
    def __init__(self, bot: 'GetBeaned'):
        self.bot = bot
        self.trello_board = trello_client.get_board('tWZ9O8yZ')  # GetBeaned Suggestions
        self.trello_list = self.trello_board.get_list("5d8697a124f30c4f48ae836e")  # New
        self.labels = {l.name: l for l in self.trello_board.get_labels()}  # Index by name

    @commands.command(aliases=["suggest", "bug", "bug_report"])
    @commands.max_concurrency(1, commands.BucketType.member)
    async def improve(self, ctx: 'CustomContext'):
        label_keys = list(self.labels.keys())
        report_type_message = "Hello there! Thanks for using this command and improving the bot. " \
                              "To start, I'll have to ask you a few questions. " \
                              "You can answer me in there normally, you don't need to use any prefix. You can exit at any time by typing `exit`\n\n" \
                              "First off, what do you want to submit. (Please answer with a number)\n- " + "\n- ".join(
            [f"**{i + 1}**) {name}" for i, name in enumerate(label_keys)])
        await ctx.send(report_type_message)
        res = await wait_for_answer(ctx, additional_check=lambda m: m.content.isdigit() and 0 < int(m.content) <= len(label_keys))
        if res is None:
            return
        else:
            report_type = label_keys[int(res.content) - 1]
            report_label = self.labels[report_type]

        report_title_message = f"Thanks! To submit your {report_type.lower()}, I'll need you to give me a quick summary of what you want.\n" \
                               f"Good summaries looks like 'Add a purge command', 'Bug in +doctor', 'Improve logging formatting', " \
                               f"while bad summaries looks like 'Add more functions', 'Give me admin perms', 'Can you please add the purge command I really need [...]'\n" \
                               f"Try to keep it under 250 characters."

        await ctx.send(report_title_message)
        res = await wait_for_answer(ctx, additional_check=lambda m: 15 < len(m.content) <= 500)
        if res is None:
            return
        else:
            report_title = res.content

        report_content_message = f"Thanks again! The last step to submit is to clarify, and add information to your {report_type.lower()}.\n" \
                                 f"For example, if you suggested a purge command, you could give examples on how it would work, what messages it would or wouldn't delete."

        await ctx.send(report_content_message)
        res = await wait_for_answer(ctx)
        if res is None:
            return
        else:
            report_content = res.content

        await ctx.send(f"Thanks! I am now sending your {report_type.lower()}. Please wait!")
        trello_card = self.trello_list.add_card(name=report_title, desc=report_content, labels=[report_label], position="bottom")
        trello_card.comment(f"{report_type} submitted by {ctx.author.name}#{ctx.author.discriminator} `[{ctx.author.id}]`")
        await ctx.send(f"Your report was successfully sent. To track the progress, please see {trello_card.url}.")


def setup(bot: 'GetBeaned'):
    bot.add_cog(Suggestions(bot))
