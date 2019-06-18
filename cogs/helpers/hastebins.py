import aiohttp
import random

hastebins_servers = ["https://wastebin.travitia.xyz/", "https://hastebin.com/"]


async def upload_text(text: str):
    server = random.choice(hastebins_servers)
    async with aiohttp.ClientSession() as cs:
        async with cs.post(server + "/documents", data=text) as r:
            res = await r.json()
            # self.logger.debug(f"(add_guild) <- {res}")
            return res["key"]
