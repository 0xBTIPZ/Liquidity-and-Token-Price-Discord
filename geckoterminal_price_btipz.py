from discord.ext import commands
import discord
from asyncio import sleep
import aiomysql
from aiomysql.cursors import DictCursor
import aiohttp, asyncio
import json
import sys
import traceback
import datetime, time
from pathlib import Path
import os
import os.path
from decimal import Decimal

from config import load_config
config = load_config()

# API from: https://api.geckoterminal.com/docs/index.html

pool = None

async def open_connection():
    global pool
    try:
        if pool is None:
            pool = await aiomysql.create_pool(
                host=config['mysql']['host'], port=3306, minsize=1, maxsize=3,
                user=config['mysql']['user'], password=config['mysql']['password'],
                db=config['mysql']['db'], cursorclass=DictCursor, autocommit=True
            )
    except Exception:
        traceback.print_exc(file=sys.stdout)

async def insert_logs(records):
    global pool
    try:
        await open_connection()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = """
                INSERT INTO `btipz_getlogs` (`address`, `block_number`, `block_timestamp`, `datetime`,
                `transaction_hash`, `transaction_index`, `log_index`, `topics`, `data`, `removed`)
                VALUES (%s, %s, %s, FROM_UNIXTIME(%s), %s, %s, %s, %s, %s, %s)
                """
                await cur.executemany(sql, records)
                await conn.commit()
                return True
    except Exception:
        traceback.print_exc(file=sys.stdout)
    return False

async def get_logs_from_db(duration: int=3600):
    global pool
    try:
        lap = int(time.time()) - duration
        await open_connection()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = """
                SELECT * FROM `btipz_getlogs` 
                WHERE `block_timestamp`>%s
                ORDER BY `block_number` ASC
                """
                await cur.execute(sql, lap)
                result = await cur.fetchall()
                if result:
                    return result
    except Exception:
        traceback.print_exc(file=sys.stdout)
    return []

async def insert_notify(
    ticker: str, decimal: int, block_number: int, block_timestamp: int, hash: str,
    from_address: str, to_address: str, real_amount: float
):
    global pool
    try:
        await open_connection()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = """
                INSERT INTO `btipz_tx_notified`
                (`ticker`, `decimal`, `block_number`, `block_timestamp`, `transaction_hash`,
                `from_address`, `to_address`, `real_amount`, `notified_date`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                await cur.execute(sql, (
                    ticker, decimal, block_number, block_timestamp, hash,
                    from_address, to_address, real_amount, int(time.time())
                ))
                await conn.commit()
                return True
    except Exception:
        traceback.print_exc(file=sys.stdout)
    return False

async def get_logs_notified(duration: int=3600):
    global pool
    try:
        lap = int(time.time()) - duration
        await open_connection()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = """
                SELECT * FROM `btipz_tx_notified` 
                WHERE `block_timestamp`>%s
                ORDER BY `id` ASC
                """
                await cur.execute(sql, lap)
                result = await cur.fetchall()
                if result:
                    return result
    except Exception:
        traceback.print_exc(file=sys.stdout)
    return []

async def get_block(url: str, numb: int, timeout: int=30):
    try:
        data_json = {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [str(hex(numb)), False],
            "id": 1
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url,
                    json=data_json,
                    headers={'Content-Type': 'application/json'},
                    timeout=timeout
            ) as response:
                if response.status == 200:
                    res_data = await response.read()
                    res_data = res_data.decode('utf-8-sig')
                    await session.close()
                    return json.loads(res_data)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
    return None

async def get_current_block(url: str, timeout: int=30):
    try:
        data_json = {
            "method": "eth_blockNumber",
            "params": [],
            "id": 1,
            "jsonrpc": "2.0"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url,
                    json=data_json,
                    headers={'Content-Type': 'application/json'},
                    timeout=timeout
            ) as response:
                if response.status == 200:
                    res_data = await response.read()
                    res_data = res_data.decode('utf-8-sig')
                    await session.close()
                    decoded_data = json.loads(res_data)
                    if decoded_data and 'result' in decoded_data:
                        return int(decoded_data['result'], 16)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
    return None

async def get_logs(url: str, from_block: int, to_block: int, contracts):
    try:
        data_json = {
            "method": "eth_getLogs",
            "params":[
                {
                    "fromBlock": hex(from_block),
                    "toBlock": hex(to_block),
                    "address": contracts
                }
            ],
            "id": 1,
            "jsonrpc": "2.0"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url,
                    json=data_json,
                    headers={'Content-Type': 'application/json'},
                    timeout=60
            ) as response:
                if response.status == 200:
                    res_data = await response.read()
                    res_data = res_data.decode('utf-8-sig')
                    await session.close()
                    decoded_data = json.loads(res_data)
                    return decoded_data
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return None
    return []

async def get_all_pools(contract: str, network: str):
    """
    network: bsc, eth
    """
    try:
        url = "https://api.geckoterminal.com/api/v2/networks/" + network.lower() + "/tokens/" + contract + "/pools"
        print("fetching {}".format(url))
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
    return []

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
        self.bg_task_1 = self.loop.create_task(self.background_task())
        self.bg_task_2 = self.loop.create_task(self.fetch_get_logs())
        self.bg_task_3 = self.loop.create_task(self.check_new_tx())

    async def check_new_tx(self):
        await self.wait_until_ready()
        while not self.is_closed():
            self.channel = self.get_channel(config['discord']['notified_tx_channel'])
            if self.channel is None:
                print("{}: can't get channel ID: {}".format(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), config['discord']['notified_tx_channel']
                ))
                await asyncio.sleep(10.0)
            new_txes = await get_logs_from_db(duration=config['token']['life_tx_duration'])
            if len(new_txes) > 0:
                get_notified = await get_logs_notified(duration=config['token']['life_tx_duration'])
                existing_notified = []
                if len(get_notified) > 0:
                    existing_notified = [i['transaction_hash'] for i in get_notified]
                for i in new_txes:
                    # already exist
                    if i['transaction_hash'] in existing_notified:
                        continue
                    # not transfer
                    if i['topic0'] != "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                        continue
                    real_amount = Decimal(int(i['data'], 16)/10**config['token']['decimal'])
                    if real_amount < 0.01:
                        continue
                    # get channel
                    # send notification
                    # insert to notify table
                    emoji_tx = "🦐"
                    div_amount = 1
                    if real_amount > 10**6:
                        emoji_tx = "🐋"
                        div_amount = 10**6
                    elif real_amount > 10**5:
                        emoji_tx = "🦈"
                        div_amount = 10**5
                    elif real_amount > 10**4:
                        emoji_tx = "🐙"
                        div_amount = 10**4
                    elif real_amount > 10**3:
                        emoji_tx = "🦑"
                        div_amount = 10**3
                    elif real_amount > 10**2:
                        emoji_tx = "🦞"
                        div_amount = 10**2
                    elif real_amount > 10:
                        emoji_tx = "🦀"
                    numb_emojis = int(real_amount/div_amount) * emoji_tx
                    embed = discord.Embed(
                        title="{} Transferred!".format(config['token']['name']),
                        timestamp=datetime.datetime.now(),
                        description=numb_emojis,
                    )
                    embed.add_field(
                        name="Amount",
                        value="{:,.4f} {}".format(real_amount, config['token']['name']),
                        inline=False
                    )
                    from_addr = i['topic1']
                    if from_addr.lower() == config['token']['tipbot_address'].lower():
                        from_addr = "TipBot"
                    else:
                        from_addr = "{}..{}".format(i['topic1'][0:3], i['topic1'][-3:])
                    to_addr = i['topic2']
                    if to_addr.lower() == config['token']['tipbot_address'].lower():
                        to_addr = "TipBot"
                    else:
                        to_addr = "{}..{}".format(i['topic2'][0:3], i['topic2'][-3:])
                    embed.add_field(
                        name="From To",
                        value="[{} -> {}]({}) <t:{}:f>".format(
                            from_addr,
                            to_addr,
                            config['token']['prefix_tx'] + i['transaction_hash'],
                            i['block_timestamp']
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name="Sender / Receiver",
                        value="[Sender]({}{}) / [Reciver]({}{})".format(
                            config['token']['prefix_address'], i['topic1'],
                            config['token']['prefix_address'], i['topic2'],
                        ),
                        inline=False
                    )
                    embed.set_thumbnail(url=config['token']['emoji_link'])
                    embed.set_author(name="Token Transfer", icon_url=self.user.display_avatar)
                    await self.channel.send(embed=embed)
                    await insert_notify(
                        config['token']['name'], config['token']['decimal'], i['block_number'], i['block_timestamp'],
                        i['transaction_hash'], i['topic1'], i['topic2'], real_amount
                    )
                    await asyncio.sleep(1.0)            
        await asyncio.sleep(10.0)

    async def fetch_get_logs(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                # check if file exist
                path = Path(config['node']['last_block_file'])
                if path.is_file():
                    text_file = open(config['node']['last_block_file'], "r")
                    block_num = int(text_file.read().strip()) + 1
                else:
                    block_num = config['node']['oldest_block']
                current_block_num = await get_current_block(config['node']['rpc'], timeout=30)
                if current_block_num is None:
                    print("{}: couldn't get top block.".format(
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    await asyncio.sleep(5.0)
                    continue
                from_block = block_num
                to_block = block_num + config['node']['lap_blocks']
                if current_block_num < to_block:
                    to_block = current_block_num
                if from_block >= current_block_num - config['node']['delay_block']:
                    print("{}: to near block. Cur: {}, From: {}. Wait for new blocks".format(
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_block_num, from_block
                    ))
                    await asyncio.sleep(5.0)
                    continue
                # do tasks
                get_log_list = await get_logs(config['node']['rpc'], from_block, to_block, config['node']['contracts'])
                if get_log_list and len(get_log_list) > 0:
                    # insert data and write
                    if 'result' not in get_log_list:
                        print("{} Height: {} = get_logs ({}, {}) got:".format(
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_block_num, from_block, to_block))
                        print(get_log_list)
                        continue
                    else:
                        if get_log_list['result'] is None:
                            print(get_log_list)
                            await asyncio.sleep(1.0)
                            continue
                        print("{} Height: {} = get_logs ({}, {}) got: {}".format(
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_block_num, from_block, to_block, len(get_log_list['result'])))
                    txes = get_log_list['result']
                    if len(txes) == 0:
                        # skip to another lap
                        if os.path.exists(config['node']['last_block_file']):
                            os.remove(config['node']['last_block_file'])
                        outfile = open(config['node']['last_block_file'], 'w')
                        outfile.write(str(to_block))
                        outfile.close() #Close the file when we’re done!
                        continue
                    else:
                        tx_list = []
                        existing_blocks = {}
                        for each_tx in txes:                                    
                            removed = 0
                            if each_tx['removed'] == True:
                                removed = 1
                            # (json.dumps(each_tx), 
                            if str(int(each_tx['blockNumber'], 16)) not in existing_blocks:
                                while True:
                                    try:
                                        get_eth_block = await get_block(config['node']['rpc'], int(each_tx['blockNumber'], 16))
                                        if get_eth_block and 'result' in get_eth_block and get_eth_block['result']:
                                            existing_blocks[str(int(each_tx['blockNumber'], 16))] = get_eth_block
                                            break
                                        await asyncio.sleep(1.0)
                                    except Exception as e:
                                        traceback.print_exc(file=sys.stdout)
                                        await asyncio.sleep(0.5)
                            else:
                                get_eth_block = existing_blocks[str(int(each_tx['blockNumber'], 16))]
                            if 'result' in get_eth_block:
                                timestamp = int(get_eth_block['result']['timestamp'], 16)
                            else:
                                timestamp = get_eth_block['timestamp']
                            # year = datetime.datetime.utcfromtimestamp(int(block['timestamp'], 16)).strftime('%Y')
                            tx_list.append((
                                each_tx['address'], int(each_tx['blockNumber'], 16),
                                timestamp, timestamp,
                                each_tx['transactionHash'], int(each_tx['transactionIndex'], 16),
                                int(each_tx['logIndex'], 16), json.dumps(each_tx['topics']) if each_tx['topics'] else None,
                                each_tx['data'], removed
                            ))
                            await insert_logs(tx_list)
                            try:
                                if os.path.exists(config['node']['last_block_file']):
                                    os.remove(config['node']['last_block_file'])
                                outfile = open(config['node']['last_block_file'], 'w')
                                outfile.write(str(to_block))
                                outfile.close() #Close the file when we’re done!
                            except Exception as e:
                                traceback.print_exc(file=sys.stdout)
                else:
                    await asyncio.sleep(5.0)
                    continue
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
            await asyncio.sleep(config['token']['fetch_sleep'])

    async def background_task(self):
        await self.wait_until_ready()
        while not self.is_closed():
            previous_nick = {}
            previous_status = None
            try:
                price_usd = "N/A"
                selected_price = 0.0
                lp_all = 0.0
                all_pools = await get_all_pools(config['token']['contract'], config['discord']['network'])
                if all_pools and len(all_pools['data']) > 0:
                    for i in all_pools['data']:
                        token_price_usd = float(i['attributes']['token_price_usd'])
                        i_lp = float(i['attributes']['reserve_in_usd'])
                        if selected_price < token_price_usd:
                            selected_price = token_price_usd
                        if i_lp > 0.0:
                            lp_all += i_lp
                price_usd = "$ {:,.8f}".format(selected_price)
                for guild in self.guilds:
                    me = guild.me
                    try:
                        liq = "LP {:,.2f}$".format(lp_all)
                        if str(guild.id) not in previous_nick or (str(guild.id) in previous_nick and previous_nick[str(guild.id)] != liq):
                            await me.edit(nick=liq)
                            print("{} Change Bot name guild {} to {}!".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), guild.name, liq))
                            previous_nick[str(guild.id)] = liq
                        if previous_status != price_usd:
                            await client.change_presence(activity=discord.Game(name=price_usd))
                            previous_status = price_usd
                            print("{} Set status to {}!".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), previous_status))
                        await sleep(config['discord']['sleep'])
                    except Exception as e:
                        traceback.print_exc(file=sys.stdout)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
            await sleep(config['discord']['sleep'])

intents = discord.Intents.default()
client = MyClient(intents=discord.Intents.default())
client.run(config['discord']['token'])

