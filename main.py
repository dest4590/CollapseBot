import os
import time
from datetime import datetime

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

intents = discord.Intents.all()

activity = discord.Activity(type=discord.ActivityType.watching, name="/stats")

bot = discord.Bot(intents=intents, activity=activity, status=discord.Status.idle)
start_time = time.time()

client = Minio(
    "minio.collapseloader.org", os.getenv("S3-ACCESS-KEY"), os.getenv("S3-SECRET-KEY")
)

bold = lambda msg: f"**{msg}**"


def get_emoji(name: str, id: int):
    return f"<:{name}:{id}>"


user_cooldowns = {}
cooldown_messages = {}
trigger_counts = {}
COOLDOWN_DURATION = 30


def check_cooldown(user_id: int) -> bool:
    current_time = time.time()
    if (
        user_id in user_cooldowns
        and current_time - user_cooldowns[user_id] < COOLDOWN_DURATION
    ):
        if user_id not in trigger_counts:
            trigger_counts[user_id] = 1
        else:
            trigger_counts[user_id] += 1
        if trigger_counts[user_id] >= 3:
            return True
    else:
        user_cooldowns[user_id] = current_time
        trigger_counts[user_id] = 1
        if user_id in cooldown_messages:
            del cooldown_messages[user_id]
    return False


def check_word_list(keywords: list, message: discord.Message) -> bool:
    return any(x in message.content for x in keywords)


is_admin = lambda id: id == 556864778576986144


async def discord_log(log: str, message: discord.Message):
    channel = bot.get_channel(1277572439236153344)
    logger.debug(f"Logging to discord: {log}")
    await channel.send(
        f"{log}, author: <@{message.author.id}>, [message link](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})"
    )


word_list_filename = "wordlist.yml"

with open(word_list_filename, "r", encoding="utf-8") as file:
    raw_word_list = file.read()
    word_list: dict = yaml.safe_load(raw_word_list)
    logger.info(f'Loaded {len(word_list.keys())} words: {", ".join(word_list.keys())}')


def use_word(keyword: str) -> bool:
    try:
        return word_list[keyword]["enabled"]
    except KeyError:
        return True


use_word_list = True


@bot.event
async def on_ready():
    logger.info(f"bluetooth device is ready to pair")


async def send_cooldown_message(message: discord.Message):
    global cooldown_messages
    if message.author.id not in cooldown_messages:
        cooldown_message = await message.channel.send(
            f"<@{message.author.id}>, you are on cooldown for {COOLDOWN_DURATION} seconds.",
            delete_after=5,
        )
        cooldown_messages[message.author.id] = cooldown_message


@bot.event
async def on_message(message: discord.Message):
    if (
        message.author.id != bot.user.id
        and use_word_list
        and message.channel.category_id == 1231330786947367015
    ):
        if check_word_list(word_list["nursultan"]["trigger"], message) and use_word(
            "nursultan"
        ):
            if not check_cooldown(message.author.id):
                await message.reply(
                    word_list["nursultan"]["response"], mention_author=False
                )
                await discord_log(f"Nursultan trigger", message)
            else:
                await send_cooldown_message(message)

        if check_word_list(word_list["download"]["trigger"], message) and use_word(
            "download"
        ):
            if not check_cooldown(message.author.id):
                await message.reply(
                    word_list["download"]["response"], mention_author=True
                )
                await discord_log(f"Download trigger", message)
            else:
                await send_cooldown_message(message)

        if check_word_list(word_list["crash"]["trigger"], message) and use_word(
            "crash"
        ):
            if not check_cooldown(message.author.id):
                await message.reply(word_list["crash"]["response"], mention_author=True)
                await discord_log(f"Crash trigger", message)
            else:
                await send_cooldown_message(message)

        if check_word_list(["<@556864778576986144>"], message):
            if not any(
                x.id
                in [
                    1245792247916793877,
                    1240356360604881027,
                    1233159828176769146,
                    1231334945041944628,
                ]
                for x in message.author.roles
            ):
                await message.reply("не тегай админов плс", mention_author=True)
                await discord_log(f"Admin tag", message)


@bot.slash_command(name="popularity", description="Check popularity of CollapseLoader")
async def popularity(ctx: discord.ApplicationContext):
    logger.debug(f"popularity command executed")

    await ctx.defer()

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
{get_emoji('users', 1292468955490812007)} CollapseLoader popularity

Yougame: {bold(yougame)}
Ezyhack: {bold(ezyhack)}
Cheater.fun: {bold(cheaterfun)}
Blasthk: {bold(blasthk)}"""
    )


@bot.slash_command(name="ping", description="Check ping of CollapseLoader servers")
async def ping(ctx: discord.ApplicationContext):
    logger.debug(f"ping command executed")

    with UptimeKumaApi("https://status.collapseloader.org") as api:
        pings = ""

        api.login_by_token(os.getenv("UPTIME-KUMA-TOKEN"))

        for m in api.get_monitors():
            pings += f'\n{m["name"]}: **{str(api.get_monitor_beats(int(m["id"]), 1)[-1]["ping"]) + "ms"}**'

        await ctx.respond(
            f"{get_emoji('ping', 1292468045662654568)} CollapseLoader servers ping\n{pings}"
        )


@bot.slash_command(name="clients", description="Get list of clients")
async def clients(ctx: discord.ApplicationContext):
    logger.debug(f"clients command executed")

    clients = requests.get(
        "https://web.collapseloader.org/api/clients",
        headers={"User-Agent": "CollapseBot"},
    ).json()
    fabric_clients = requests.get(
        "https://web.collapseloader.org/api/fabric_clients",
        headers={"User-Agent": "CollapseBot"},
    ).json()

    clients = clients + fabric_clients

    embed = discord.Embed(color=discord.Colour.dark_grey())

    embed.add_field(
        name="Clients list",
        value="\n".join(
            [
                f"{client['name']} - {client['version']} {'[Hidden]' if not client['show_in_loader'] else ''}{f' - Fabric' if client['fabric'] else ''}"
                for client in clients
            ]
        ),
    )

    embed.set_footer(text=f"Client count: {len(clients)}")

    await ctx.respond(
        f"{get_emoji('clients', 1292469727125438575)} Our clients:", embed=embed
    )


@bot.slash_command(name="client", description="Get information about client")
async def client_cmd(ctx: discord.ApplicationContext, client: discord.Option(str, description="Client to get information about")):  # type: ignore
    logger.debug(f"client command executed")

    clients = requests.get(
        "https://web.collapseloader.org/api/clients",
        headers={"User-Agent": "CollapseBot"},
    ).json()

    client = next((c for c in clients if client.lower() in c["name"].lower()), None)

    if client:
        embed = discord.Embed(color=discord.Color.dark_grey())
        embed.set_author(name=client["name"], icon_url=bot.user.avatar.url)
        embed.add_field(
            name=f"{get_emoji('version', 1306166191177469952)} Version",
            value=client["version"],
        )
        embed.add_field(
            name=f"{get_emoji('file', 1306166288649027584)} Filename",
            value=client["filename"],
        )
        embed.add_field(
            name=f"{get_emoji('main_class', 1306166348757598228)} Main class",
            value=client["main_class"],
        )
        embed.add_field(
            name=f"{get_emoji('category', 1306166447399112744)} Category",
            value=client["category"],
        )
        embed.add_field(
            name=f"{get_emoji('question', 1306166594065530950)} Working",
            value=client["working"],
        )
        embed.add_field(
            name=f"{get_emoji('question', 1306166594065530950)} Internal",
            value=client["internal"],
        )
        embed.add_field(
            name=f"{get_emoji('question', 1306166594065530950)} Fabric",
            value=client["fabric"],
        )
        created_at = datetime.strptime(client["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        updated_at = datetime.strptime(client["updated_at"], "%Y-%m-%dT%H:%M:%S.%fZ")

        embed.add_field(
            name=f"{get_emoji('timeline', 1292468817234104401)} Created at",
            value=created_at.strftime("%d.%m.%Y %H:%M:%S"),
        )
        embed.add_field(
            name=f"{get_emoji('timeline', 1292468817234104401)} Updated at",
            value=updated_at.strftime("%d.%m.%Y %H:%M:%S"),
        )

        await ctx.respond(embed=embed)

    else:
        await ctx.respond("Client not found")


def get_bucket_size(bucket: str) -> int:
    total_size = 0

    objects = client.list_objects(bucket, recursive=True)
    for obj in objects:
        total_size += obj.size

    return f"{total_size / 1024 / 1024:.2f}"


@bot.slash_command(name="size", description="Get size of CollapseLoader storage")
async def size(ctx: discord.ApplicationContext):
    logger.debug(f"size command executed")

    await ctx.respond(
        f"{get_emoji('data', 1292467157891813498)} Total size of CollapseLoader: **{get_bucket_size('collapse')}** MB"
    )


@bot.slash_command(name="stats", description="Get CollapseLoader stats")
async def stats(ctx: discord.ApplicationContext):
    logger.debug(f"stats command executed")

    analytics = requests.get(
        "https://web.collapseloader.org/api/counter",
        headers={"User-Agent": "CollapseBot"},
    ).json()

    endpoint_counts = {entry["endpoint"]: entry["count"] for entry in analytics}

    embed = discord.Embed(color=discord.Color.dark_grey())

    embed.add_field(
        name=f"{get_emoji('servers', 1292468955490812007)} Server Count",
        value=str(len(bot.guilds)),
    )
    embed.add_field(
        name=f"{get_emoji('users', 1292468955490812007)} Total Users",
        value=str(sum(guild.member_count for guild in bot.guilds)),
    )
    embed.add_field(
        name=f"{get_emoji('timeline', 1292468817234104401)} Uptime",
        value=get_uptime_string(),
    )
    embed.add_field(
        name=f"{get_emoji('wordlist', 1292468606021406771)} Word List enabled",
        value=use_word_list,
    )
    embed.add_field(
        name=f"{get_emoji('wordlist', 1292468606021406771)} Word List words",
        value=str(len(word_list.keys())),
    )
    embed.add_field(
        name=f"{get_emoji('data', 1292467157891813498)} Bucket Size",
        value=f"{get_bucket_size('collapse')} MB",
    )
    embed.add_field(
        name=f"{get_emoji('ping', 1292468045662654568)} Discord ping",
        value=f"{bot.latency * 1000:.2f}ms",
    )
    embed.add_field(
        name=f"{get_emoji('analytics', 1292468265108635729)} Loader start",
        value=f"{endpoint_counts.get('api/analytics/start', '?')} times",
    )
    embed.add_field(
        name=f"{get_emoji('analytics', 1292468265108635729)} Client start",
        value=f"{endpoint_counts.get('api/analytics/client', '?')} times",
    )
    embed.add_field(
        name=f"{get_emoji('commands', 1292469546283958403)} Command Count",
        value=str(len(bot.commands)),
    )

    embed.set_thumbnail(url=bot.user.avatar.url)

    await ctx.respond(embed=embed)


@bot.slash_command(name="user", description="Get information about user")
async def user(ctx: discord.ApplicationContext, user: discord.Option(discord.User, description="User to get information about")):  # type: ignore
    logger.debug(f"user command executed")

    if is_admin(ctx.author.id):
        user: discord.Member = user or ctx.author

        embed = discord.Embed(color=discord.Color.dark_grey())
        embed.set_author(name=user.name, icon_url=user.avatar.url)
        embed.add_field(
            name=f"{get_emoji('id', 1292470345755791360)} ID", value=user.id
        )
        embed.add_field(
            name=f"{get_emoji('timeline', 1292468817234104401)} Created at",
            value=user.created_at.strftime("%d.%m.%Y %H:%M:%S"),
        )
        embed.add_field(
            name=f"{get_emoji('timeline', 1292468817234104401)} Joined at",
            value=(
                user.joined_at.strftime("%d.%m.%Y %H:%M:%S")
                if user.joined_at
                else "Not in server"
            ),
        )

        user_roles = user.roles
        user_roles.remove(ctx.guild.default_role)

        embed.add_field(
            name=f"{get_emoji('roles', 1292470773700755549)} Roles",
            value=(
                ", ".join(role.name for role in user_roles)
                if user_roles
                else "No roles"
            ),
        )
        embed.add_field(
            name=f"{get_emoji('status', 1292471789628428409)} Status",
            value=user.status.value.capitalize(),
        )

        embed.set_thumbnail(url=user.avatar.url)

        await ctx.respond(embed=embed)


@bot.slash_command(name="socials", description="Get CollapseLoader socials")
async def socials(ctx: discord.ApplicationContext):
    logger.debug(f"socials command executed")

    embed = discord.Embed(color=discord.Color.brand_green())
    embed.add_field(
        name="Socials",
        value="\n[Telegram](https://t.me/collapseloader)\n[Discord](https://discord.com/invite/FyKtnFqs6J)",
    )
    embed.set_thumbnail(url=bot.user.avatar.url)

    await ctx.respond(embed=embed)


@bot.slash_command(
    name="files", description="Get list of files in CollapseLoader storage"
)
async def files(ctx: discord.ApplicationContext):
    logger.debug(f"files command executed")

    objects = client.list_objects("collapse", recursive=True)

    embed = discord.Embed(color=discord.Color.dark_grey())
    embed.add_field(
        name="Files list",
        value="\n".join(
            [f"{obj.object_name} - {obj.size / 1024 / 1024:.2f} MB" for obj in objects]
        ),
    )

    await ctx.respond("Our files:", embed=embed)


@bot.slash_command(name="use_word_list", description="Toggle word list")
async def cmd_use_word_list(ctx: discord.ApplicationContext):
    if is_admin(ctx.author.id):
        global use_word_list
        use_word_list = not use_word_list

        await ctx.respond(
            f"Word list is now {'enabled' if use_word_list else 'disabled'}"
        )
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
        uptime_string += f"{uptime_minutes % 60} minutes and "

    uptime_string += f"{uptime_seconds % 60} seconds"

    return uptime_string


@bot.slash_command(name="uptime", description="Get uptime of CollapseBot")
async def uptime(ctx: discord.ApplicationContext):
    logger.debug(f"uptime command executed")

    await ctx.respond(f"Bot running for {get_uptime_string()}")


@bot.slash_command(name="wordlist", description="Get word list")
async def wordlist(ctx: discord.ApplicationContext):
    logger.debug(f"wordlist command executed")

    await ctx.respond(
        f"```yaml\n{raw_word_list}```\nEnabled: `{use_word_list}`\nLoaded commands: {len(word_list.keys())}\nEnabled commands: {len([word for word in word_list.keys() if word_list[word]['enabled']])}"
    )


@bot.slash_command(name="toggle_word", description="Toggle word in word list")
async def toggle_word(
    ctx: discord.ApplicationContext,
    word: discord.Option(
        str, description="Word to toggle", choices=[word for word in word_list.keys()]
    ),  # type: ignore
):
    if is_admin(ctx.author.id):
        try:
            word_list[word]["enabled"] = not word_list[word]["enabled"]

            await ctx.respond(
                f"Word `{word}` is now {'enabled' if word_list[word]['enabled'] else 'disabled'}"
            )
        except KeyError:
            await ctx.respond(f"Word `{word}` not found")
    else:
        await ctx.respond("вали отсюда")


bot.run(os.getenv("TOKEN"))
