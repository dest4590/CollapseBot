import os

import discord
import requests
from dotenv import load_dotenv
from uptime_kuma_api import UptimeKumaApi

from collapsepopularity.parsers.cheaterfun import CheaterFun
from collapsepopularity.parsers.ezyhack import Ezyhack
from collapsepopularity.parsers.xenforo import Xenforo

load_dotenv()
bot = discord.Bot()

def bold(msg: str) -> str:
    return f'**{msg}**'

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="popularity", description="Check popularity of CollapseLoader")
async def popularity(ctx: discord.ApplicationContext):
    yougame = Xenforo('https://yougame.biz/forums/64/', 319219).parse()
    # blasthk = Xenforo('https://www.blast.hk/forums/177/', 211204).parse()
    ezyhack = Ezyhack().parse(os.getenv('PROXY'))
    cheaterfun = CheaterFun().parse(os.getenv('PROXY'))

    await ctx.respond(f"""
CollapseLoader popularity

Yougame: {bold(yougame)}
Ezyhack: {bold(ezyhack)}
Cheater.fun: {bold(cheaterfun)}""")
        
@bot.slash_command(name="ping", description="Check ping of CollapseLoader servers")
async def ping(ctx: discord.ApplicationContext):
    with UptimeKumaApi('https://status.collapseloader.org') as api:
        pings = ''

        api.login_by_token(os.getenv('UPTIME-KUMA-TOKEN'))

        for m in api.get_monitors():
            pings += f'\n{m['name']}: **{str(api.get_monitor_beats(int(m['id']), 1)[-1]['ping']) + 'ms'}**'

        await ctx.respond(f"CollapseLoader servers ping\n{pings}")

@bot.slash_command(name="clients", description="Get list of clients")
async def clients(ctx: discord.ApplicationContext):
    clients = requests.get('https://web.collapseloader.org/api/clients').json()

    embed = discord.Embed(color=discord.Colour.dark_purple())

    embed.add_field(name='Clients list', value='\n'.join([f'{client['name']} - {client['version']}' for client in clients]))

    embed.set_footer(text=f"Client count: {len(clients)}")

    await ctx.respond("Our clients:", embed=embed)
    
bot.run(os.getenv('TOKEN'))