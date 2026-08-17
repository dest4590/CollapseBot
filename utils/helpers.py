import time
from typing import Optional

import discord

import config
from logger import logger

COLOR_ERROR = 0xFF4444
COLOR_SUCCESS = 0x00FF88
COLOR_WARNING = 0xFF8800
COLOR_INFO = 0x00AA00


def get_emoji(name: str, id: int):
    """Get Discord emoji string format"""
    return f"<:{name}:{id}>"


def make_embed(
    title: str, description: str = "", color: int = COLOR_INFO, **kwargs
) -> discord.Embed:
    """Build a discord.Embed, forwarding extra kwargs (e.g. footer text via ``set_footer``-style dicts)."""
    return discord.Embed(title=title, description=description, color=color, **kwargs)


def error_embed(title: str, description: str) -> discord.Embed:
    """Standard ❌-prefixed error embed."""
    if not title.startswith("❌"):
        title = f"❌ {title}"
    return make_embed(title, description, COLOR_ERROR)


def access_denied_embed(
    description: str = "You don't have permission to use this command.",
    title: str = "Access Denied",
) -> discord.Embed:
    return error_embed(title, description)


async def require_staff(
    ctx: discord.ApplicationContext,
    description: str = "You don't have permission to use this command.",
    title: str = "Access Denied",
) -> bool:
    """Respond with an access-denied embed and return False unless the invoker is staff."""
    if isinstance(ctx.author, discord.Member) and is_staff(ctx.author):
        return True
    await ctx.respond(embed=access_denied_embed(description, title), ephemeral=True)
    return False


async def require_admin(
    ctx: discord.ApplicationContext,
    description: str = "This command is only available to the main administrator.",
    title: str = "Access Denied",
) -> bool:
    """Respond with an access-denied embed and return False unless the invoker is the main admin."""
    if is_admin(ctx.author.id):
        return True
    await ctx.respond(embed=access_denied_embed(description, title), ephemeral=True)
    return False


def check_word_list(keywords: list, message: discord.Message) -> bool:
    """Check if any keyword in the list is in the message content (case-insensitive)"""
    message_content = message.content.lower()
    return any(keyword.lower() in message_content for keyword in keywords)


def is_admin(user_id: int) -> bool:
    """Check if user ID is admin"""
    return user_id == config.ADMIN_USER_ID


def is_staff(member: discord.Member) -> bool:
    """Check if member has any admin role"""
    return any(role.id in config.ADMIN_ROLES for role in member.roles)


def get_uptime_string(start_time: float) -> str:
    """Get formatted uptime string"""
    uptime_seconds = int(time.time() - start_time)
    uptime_minutes = uptime_seconds // 60
    uptime_hours = uptime_minutes // 60
    uptime_days = uptime_hours // 24

    uptime_string = ""

    if uptime_days > 0:
        uptime_string += f"{uptime_days} days, "
    if uptime_hours > 0:
        uptime_string += f"{uptime_hours % 24} hours, "
    if uptime_minutes > 0:
        uptime_string += f"{uptime_minutes % 60} minutes and "

    uptime_string += f"{uptime_seconds % 60} seconds"

    return uptime_string


def bold(msg: str) -> str:
    """Format text as bold for Discord markdown"""
    return f"**{msg}**"


def validate_config() -> bool:
    """Validate that all required config values are present"""
    required_vars = ["TOKEN"]

    missing_vars = []
    for var in required_vars:
        if not hasattr(config, var) or getattr(config, var) is None:
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required config variables: {missing_vars}")
        return False

    return True


async def safe_send_message(
    channel: discord.TextChannel, content: str, **kwargs
) -> Optional[discord.Message]:
    """Safely send a message with error handling"""
    try:
        return await channel.send(content, **kwargs)
    except discord.HTTPException as e:
        logger.error(f"Failed to send message to {channel.id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return None
