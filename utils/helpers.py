import time
from typing import Optional

import discord
from loguru import logger

import config


def get_emoji(name: str, id: int):
    """Get Discord emoji string format"""
    return f"<:{name}:{id}>"


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


def get_bucket_size(bucket: str) -> str:
    """Calculate total size of bucket in MB"""
    try:
        from utils.storage import get_client

        client = get_client()
        if client is None:
            logger.error("Storage client is None")
            return "Error"
        total_size = 0
        objects = client.list_objects(bucket, recursive=True)
        for obj in objects:
            total_size += obj.size or 0

        return f"{total_size / 1024 / 1024:.2f}"
    except Exception as e:
        logger.error(f"Failed to get bucket size: {e}")
        return "Error"


def bold(msg: str) -> str:
    """Format text as bold for Discord markdown"""
    return f"**{msg}**"


def validate_config() -> bool:
    """Validate that all required config values are present"""
    required_vars = [
        "TOKEN",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
    ]

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
