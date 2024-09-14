import os
import time

import discord
import requests
import yaml
from dotenv import load_dotenv
from loguru import logger
from minio import Minio
from uptime_kuma_api import UptimeKumaApi

from collapsepopularity.parsers.cheaterfun import CheaterFun
from collapsepopularity.parsers.ezyhack import Ezyhack
from collapsepopularity.parsers.xenforo import Xenforo

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(type=discord.ActivityType.watching, name="/popularity")

bot = discord.Bot(intents=intents, activity=activity, status=discord.Status.idle)
start_time = time.time()

client = Minio("minio.collapseloader.org", os.getenv("S3-ACCESS-KEY"), os.getenv("S3-SECRET-KEY"))

bold = lambda msg: f"**{msg}**"

def check_word_list(word_list: list, message: discord.Message) -> bool:
    return any(x in message.content for x in word_list)

is_admin = lambda id: id == 556864778576986144

async def discord_log(log: str, message: discord.Message):
    channel = bot.get_channel(1277572439236153344)
    logger.debug(f"Logging to discord: {log}")
    await channel.send(f'{log}, author: <@{message.author.id}>, [message link](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})')

with open("wordlist.yml", "r", encoding="utf-8") as file:
    raw_word_list = file.read()
    word_list: dict = yaml.safe_load(raw_word_list)
    logger.debug(f"Word list loaded: {word_list}")
    
use_word_list = True

@bot.event
async def on_ready():
    logger.info(f"bluetooth device is ready to pair")

@bot.event
async def on_message(message: discord.Message):
    if message.author.id != bot.user.id and use_word_list and message.channel.category_id != 1231330787396161783:
        if check_word_list(word_list["nursultan"]["trigger"], message):
            await discord_log(f"Nursultan trigger", message)
            await message.reply("кряк нурика ратка", mention_author=False)

        if check_word_list(word_list["download"]["trigger"], message):
            await message.reply(word_list["download"]["response"], mention_author=True)
            await discord_log(f"Download trigger", message)

        if check_word_list(word_list["crash"]["trigger"], message):
            await message.reply(word_list["crash"]["response"], mention_author=True)
            await discord_log(f"Crash trigger", message)

        if check_word_list(["<@556864778576986144>"], message):
            if not any(x.id in [1245792247916793877, 1240356360604881027, 1233159828176769146, 1231334945041944628] for x in message.author.roles):
                await message.reply("не тегай админов плс", mention_author=True)
                await discord_log(f"Admin tag", message)

@bot.slash_command(name="popularity", description="Check popularity of CollapseLoader")
async def popularity(ctx: discord.ApplicationContext):
    logger.debug(f"popularity command executed")
    
    yougame = Xenforo("https://yougame.biz/forums/64/", 319219).parse()
    logger.debug(f"parsed yougame: {yougame}")
    
    blasthk = Xenforo("https://www.blast.hk/forums/177/", 211204).parse()
    logger.debug(f"parsed blasthk: {blasthk}")
    
    ezyhack = Ezyhack().parse(os.getenv("PROXY"))
    logger.debug(f"parsed ezyhack: {ezyhack}")
    
    cheaterfun = CheaterFun().parse(os.getenv("PROXY"))
    logger.debug(f"parsed cheaterfun: {cheaterfun}")

    await ctx.respond(
        f"""
CollapseLoader popularity

Yougame: {bold(yougame)}
Ezyhack: {bold(ezyhack)}
Cheater.fun: {bold(cheaterfun)}
Blasthk: {bold(blasthk)}""")

@bot.slash_command(name="ping", description="Check ping of CollapseLoader servers")
async def ping(ctx: discord.ApplicationContext):
    logger.debug(f"ping command executed")
    
    with UptimeKumaApi('https://status.collapseloader.org') as api:
        pings = ''

        api.login_by_token(os.getenv('UPTIME-KUMA-TOKEN'))

        for m in api.get_monitors():
            pings += f'\n{m['name']}: **{str(api.get_monitor_beats(int(m['id']), 1)[-1]['ping']) + 'ms'}**'

        await ctx.respond(f"CollapseLoader servers ping\n{pings}")

@bot.slash_command(name="clients", description="Get list of clients")
async def clients(ctx: discord.ApplicationContext):
    logger.debug(f"clients command executed")
    
    clients = requests.get("https://web.collapseloader.org/api/clients").json()

    embed = discord.Embed(color=discord.Colour.dark_grey())

    embed.add_field(
        name="Clients list",
        value="\n".join(
            [
                f"{client['name']} - {client['version']} {'[Hidden]' if not client['show_in_loader'] else ''}"
                for client in clients
            ]
        ),
    )

    embed.set_footer(text=f"Client count: {len(clients)}")

    await ctx.respond("Our clients:", embed=embed)

def get_bucket_size(bucket: str) -> int:
    total_size = 0

    objects = client.list_objects(bucket, recursive=True)
    for obj in objects:
        total_size += obj.size

    return f"{total_size / 1024 / 1024:.2f}"

@bot.slash_command(name="size", description="Get size of CollapseLoader storage")
async def size(ctx: discord.ApplicationContext):
    logger.debug(f"size command executed")

    await ctx.respond(f"Total size of CollapseLoader: **{get_bucket_size('collapse')}** MB")

@bot.slash_command(name="stats", description="Get CollapseLoader stats")
async def stats(ctx: discord.ApplicationContext):
    logger.debug(f"stats command executed")

    analytics = requests.get('https://web.collapseloader.org/api/counter').json()

    endpoint_counts = {entry['endpoint']: entry['count'] for entry in analytics}

    embed = discord.Embed(color=discord.Color.dark_grey())

    embed.add_field(name="Server Count", value=f"Total Servers: {len(bot.guilds)}")
    embed.add_field(name="User Count", value=f"Total Users: {sum(guild.member_count for guild in bot.guilds)}")
    embed.add_field(name="Uptime", value=f"Bot Uptime: {get_uptime_string()}")
    embed.add_field(name="Word List", value=f"Word List Enabled: {use_word_list}")
    embed.add_field(name="Bucket Size", value=f"Total Size: {get_bucket_size('collapse')} MB")
    embed.add_field(name="Discord ping", value=f"{bot.latency * 1000:.2f}ms")
    embed.add_field(name="Loader start", value=f"{endpoint_counts.get('api/analytics/start', '?')} times")
    embed.add_field(name="Client start", value=f"{endpoint_counts.get('api/analytics/client', '?')} times")
    embed.set_thumbnail(url=bot.user.avatar.url)

    await ctx.respond(embed=embed)

@bot.slash_command(name="files", description="Get list of files in CollapseLoader storage")
async def files(ctx: discord.ApplicationContext):
    logger.debug(f"files command executed")

    objects = client.list_objects("collapse", recursive=True)

    embed = discord.Embed(color=discord.Color.dark_grey())
    embed.add_field(
        name="Files list",
        value="\n".join(
            [
                f"{obj.object_name} - {obj.size / 1024 / 1024:.2f} MB"
                for obj in objects
            ]
        ),
    )

    await ctx.respond("Our files:", embed=embed)

@bot.slash_command(name="use_word_list", description="Toggle word list")
async def cmd_use_word_list(ctx: discord.ApplicationContext):
    if is_admin(ctx.author.id):
        global use_word_list
        use_word_list = not use_word_list

        await ctx.respond(f"Word list is now {'enabled' if use_word_list else 'disabled'}")
    else:
        await ctx.respond("вали отсюда")

def get_uptime_string():
    """Get uptime string"""
    
    uptime_seconds = int(time.time() - start_time)
    uptime_minutes = uptime_seconds // 60
    uptime_hours = uptime_minutes // 60

    uptime_string = ""
    
    if uptime_hours > 0:
        uptime_string += f"{uptime_hours} hours, "
    if uptime_minutes > 0:
        uptime_string += f"{uptime_minutes % 60} minutes, "
        
    uptime_string += f"{uptime_seconds % 60} seconds"

    return uptime_string

@bot.slash_command(name="uptime", description="Get uptime of CollapseBot")
async def uptime(ctx: discord.ApplicationContext):
    logger.debug(f"uptime command executed")
    
    await ctx.respond(f"Bot running for {get_uptime_string()}")

@bot.slash_command(name="update", description="Restart CollapseBot")
async def restart(ctx: discord.ApplicationContext):
    logger.debug(f"update command executed")
    
    if is_admin(ctx.author.id):
        await ctx.respond("Updating...")
        os.system("git pull")
        os.system("bash rebuild.sh")
    else: 
        await ctx.respond("вали отсюда")

@bot.slash_command(name="wordlist", description="Get word list")
async def wordlist(ctx: discord.ApplicationContext):
    logger.debug(f"wordlist command executed")
    
    await ctx.respond(f"Word list: ```yaml\n{raw_word_list}```")

bot.run(os.getenv("TOKEN"))