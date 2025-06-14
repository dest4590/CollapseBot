import sys
import time
from pathlib import Path

import discord
import yaml
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger

import config
from utils.helpers import validate_config

load_dotenv()

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time}</green> | <level>{level}</level> | <level>{message}</level>",
)

if not validate_config():
    logger.error("Configuration validation failed. Exiting.")
    sys.exit(1)

intents = discord.Intents.all()
activity = discord.Activity(
    type=discord.ActivityType.watching, name="/stats"
)
bot = discord.Bot(intents=intents, activity=activity, status=discord.Status.online)

start_time = time.time()

automatic_responses_filename = "automatic_responses.yml"
try:
    with open(automatic_responses_filename, "r", encoding="utf-8") as file:
        automatic_responses_raw = file.read()
        automatic_responses: dict = yaml.safe_load(automatic_responses_raw)
except FileNotFoundError:
    logger.warning(f"Automatic responses file {automatic_responses_filename} not found")
    automatic_responses = {}
    automatic_responses_raw = ""
except yaml.YAMLError as e:
    logger.error(f"Failed to parse automatic responses YAML: {e}")
    automatic_responses = {}
    automatic_responses_raw = ""

use_automatic_responses = True

cog_dir = Path("./cogs")
loaded_cogs = 0
failed_cogs = 0

for cog_file in cog_dir.glob("*_cog.py"):
    cog_name = f"cogs.{cog_file.stem}"
    try:
        bot.load_extension(cog_name)
        logger.info(f"✅ Loaded extension: {cog_name}")
        loaded_cogs += 1
    except Exception as e:
        logger.error(f"❌ Failed to load extension {cog_name}: {e}")
        failed_cogs += 1

logger.info(f"📦 Loaded {loaded_cogs} cogs successfully, {failed_cogs} failed")


@bot.event
async def on_ready():
    logger.info(f"🚀 Bot is ready! Logged in as {bot.user}")
    logger.info(f"🌐 Connected to {len(bot.guilds)} guilds")
    logger.info(f"👥 Serving {sum(guild.member_count for guild in bot.guilds):,} users")


@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Command error in {ctx.command}: {error}")

    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Missing Permissions",
            description="You don't have the required permissions to use this command.",
            color=0xFF4444,
        )
        embed.add_field(
            name="Required Permissions",
            value=", ".join(error.missing_permissions),
            inline=False,
        )
        await ctx.respond(embed=embed, ephemeral=True)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="⏰ Command on Cooldown",
            description=f"Please wait **{error.retry_after:.1f} seconds** before using this command again.",
            color=0xFFAA00,
        )
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description="An unexpected error occurred while processing your command.",
            color=0xFF4444,
        )
        embed.add_field(
            name="💡 What to do",
            value="• Try the command again\n• Contact an administrator if the issue persists",
            inline=False,
        )
        await ctx.respond(embed=embed, ephemeral=True)


if __name__ == "__main__":
    logger.info("🔄 Starting CollapseBot...")
    try:
        bot.run(config.TOKEN)
    except discord.LoginFailure:
        logger.error("❌ Invalid bot token")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
