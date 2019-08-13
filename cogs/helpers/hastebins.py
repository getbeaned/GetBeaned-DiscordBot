import aiohttp
import random

hastebins_servers = ["https://wastebin.travitia.xyz/", "https://hastebin.com/", "https://del.dog/", "http://bin.shortbin.eu:8080/", "https://dropb.in/", "https://mystb.in/"]


async def upload_text(text: str):
    servers = hastebins_servers[:]
    random.shuffle(servers) # In-place

    async with aiohttp.ClientSession() as cs:
        for server in servers:
            try:
                async with cs.post(server + "/documents", data=text) as r:
                    res = await r.json()
                    return server + res["key"]
            except:
                break
    raise IOError("No paste servers available :(")
