from discord.ext import commands
import discord
from asyncio import sleep
import aiohttp, asyncio
import json
import sys
import traceback

from config import load_config
config = load_config()

# from: https://api.geckoterminal.com/docs/index.html
list_pools = [
    "0x843afdc56e0c57dc8736b7380b4fc6dd4be6a570",
    "0x9866f94c637e5c7f3044afb0516954c63c0ba579"
]
pool_url = "https://api.geckoterminal.com/api/v2/networks/bsc/pools/"

async def get_pool_data(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'Content-Type': 'application/json'}, timeout=30) as response:
                if response.status == 200:
                    res_data = await response.read()
                    res_data = res_data.decode('utf-8-sig')
                    await session.close()
                    decoded_data = json.loads(res_data)
                    return decoded_data
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
    return None

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def on_ready(self):
        print("Bot is online {}.".format(self.user.name))
        print("Invite link: https://discord.com/oauth2/authorize?client_id={}&scope=bot".format(self.user.id))
    
    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.background_task())
    
    async def background_task(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                price_usd = "N/A"
                selected_price = 0.0
                lp_all = 0.0
                for i in list_pools:
                    market = await get_pool_data(pool_url + i)
                    if selected_price < float(market['data']['attributes']['base_token_price_usd']):
                        selected_price = float(market['data']['attributes']['base_token_price_usd'])
                    if float(market['data']['attributes']['reserve_in_usd']) > 0.0:
                        lp_all += float(market['data']['attributes']['reserve_in_usd'])
                price_usd = "$ {:,.8f}".format(selected_price)
                for guild in self.guilds:
                    me = guild.me
                    try:
                        liq = "LP {:,.2f}$".format(lp_all)
                        await me.edit(nick=liq)
                        await client.change_presence(activity=discord.Game(name=price_usd))
                        await sleep(config['discord']['sleep'])
                    except Exception as e:
                        traceback.print_exc(file=sys.stdout)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
            await sleep(config['discord']['sleep'])

intents = discord.Intents.default()
client = MyClient(intents=discord.Intents.default())
client.run(config['discord']['token'])

