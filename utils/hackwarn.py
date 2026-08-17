from dataclasses import dataclass
from typing import Optional

import discord

import config
from logger import logger

DM_TEXT = (
    "Пожалуйста, выйдите из аккаунта и смените пароль, вас взломали!\n"
    "Старайтесь не скачивать \"бесплатные читы, клиенты, лаунчеры\", в следующий раз будьте внимательнее.\n"
    "С благодарностью, администрация CollapseLoader.\n"
    "---\n"
    "Please log out of your account and change your password, you've been hacked!\n"
    "Try not to download \"free cheats, clients, launchers\", next time be more careful.\n"
    "With gratitude, the CollapseLoader administration."
)

SPAM_KEYWORDS = ["bro"]
SPAM_ATTACHMENT_MARKERS = ["1.jpg"]


@dataclass
class HackWarnResult:
    deleted: bool
    dm_sent: bool
    target: discord.abc.User


def message_matches_hack_spam(message: discord.Message) -> bool:
    """Detect known hack-spam patterns in a message (keywords or a marker image)."""
    content = (message.content or "").lower()
    if any(keyword in content for keyword in SPAM_KEYWORDS):
        return True

    for att in getattr(message, "attachments", None) or []:
        fname = (att.filename or "").lower()
        url = (att.url or "").lower()
        if any(marker in fname or marker in url for marker in SPAM_ATTACHMENT_MARKERS):
            return True

    for embed in getattr(message, "embeds", None) or []:
        img = getattr(embed, "image", None)
        img_url = (getattr(img, "url", None) or "").lower() if img else ""
        if img_url and any(marker in img_url for marker in SPAM_ATTACHMENT_MARKERS):
            return True

    return False


async def notify_hackwarn_channel(
    bot: discord.Bot,
    result: "HackWarnResult",
    message: discord.Message,
    triggered_by: Optional[discord.abc.User],
    automatic: bool,
) -> None:
    """Post a log embed to the hackwarn notification channel."""
    channel = bot.get_channel(config.HACKWARN_NOTIFY_CHANNEL_ID)
    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        logger.warning(
            f"Hackwarn notify channel {config.HACKWARN_NOTIFY_CHANNEL_ID} not found or not text-capable"
        )
        return

    embed = discord.Embed(
        title="🛡️ Hackwarn Triggered" + (" (auto)" if automatic else ""),
        color=0x00FF88 if result.dm_sent else 0xFFAA00,
    )
    embed.add_field(name="👤 User", value=f"{result.target.mention} ({result.target.id})", inline=False)
    embed.add_field(name="📍 Channel", value=getattr(message.channel, "mention", str(message.channel.id)), inline=True)
    embed.add_field(name="✉️ DM", value="Sent" if result.dm_sent else "Failed", inline=True)
    if triggered_by is not None:
        embed.add_field(name="🧑‍💼 Triggered by", value=triggered_by.mention, inline=True)
    if message.content:
        embed.add_field(name="📝 Content", value=message.content[:1000], inline=False)

    try:
        await channel.send(embed=embed)
    except discord.HTTPException as e:
        logger.error(f"Failed to send hackwarn notification: {e}")


async def apply_hack_warn(
    bot: discord.Bot,
    message: discord.Message,
    *,
    triggered_by: Optional[discord.abc.User] = None,
    automatic: bool = False,
) -> HackWarnResult:
    """Delete a hack-spam message, DM the author a warning, and log it.

    Falls back to a channel mention if the DM fails to send.
    """
    target = message.author

    deleted = False
    try:
        await message.delete()
        deleted = True
    except discord.HTTPException as e:
        logger.error(f"Failed to delete message {message.id}: {e}")

    dm_sent = False
    try:
        await target.send(DM_TEXT)
        dm_sent = True
    except Exception:
        dm_sent = False

    if not dm_sent:
        try:
            await message.channel.send(f"{target.mention} {DM_TEXT}")
        except Exception:
            pass

    result = HackWarnResult(deleted=deleted, dm_sent=dm_sent, target=target)
    await notify_hackwarn_channel(bot, result, message, triggered_by, automatic)
    return result
