import random
import time
from datetime import datetime
from typing import Dict

import discord
import yaml
from discord.ext import commands
from loguru import logger

import config
from utils.helpers import is_staff


class AutomaticResponsesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automatic_responses: Dict = {}
        self.user_cooldowns: Dict[str, float] = {}
        self.load_automatic_responses()

    def load_automatic_responses(self):
        """Load automatic responses from YAML file"""
        try:
            with open("automatic_responses.yml", "r", encoding="utf-8") as file:
                self.automatic_responses = yaml.safe_load(file) or {}
                logger.info(
                    f"✅ Loaded {len(self.automatic_responses)} automatic responses"
                )
        except FileNotFoundError:
            logger.warning("Automatic responses file not found, creating empty config")
            self.automatic_responses = {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse automatic responses YAML: {e}")
            self.automatic_responses = {}

    def save_automatic_responses(self):
        """Save automatic responses to YAML file"""
        try:
            with open("automatic_responses.yml", "w", encoding="utf-8") as file:
                yaml.dump(
                    self.automatic_responses,
                    file,
                    default_flow_style=False,
                    allow_unicode=True,
                )
                logger.info("Automatic responses saved successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to save automatic responses: {e}")
            return False

    def check_conditions(self, response_data: Dict, message: discord.Message) -> bool:
        """Check if response conditions are met"""
        conditions = response_data.get("conditions", {})

        channel_types = conditions.get("channel_types", ["any"])
        if "any" not in channel_types:
            if (
                isinstance(message.channel, discord.Thread)
                and "thread" not in channel_types
            ):
                return False
            if (
                isinstance(message.channel, discord.TextChannel)
                and "text" not in channel_types
            ):
                return False
            if (
                isinstance(message.channel, discord.DMChannel)
                and "dm" not in channel_types
            ):
                return False

        probability = conditions.get("probability", 1.0)
        if random.random() > probability:
            return False

        required_keywords = conditions.get("require_keywords", [])
        if required_keywords:
            message_lower = message.content.lower()
            if not any(
                keyword.lower() in message_lower for keyword in required_keywords
            ):
                return False

        return True

    def check_cooldown(
        self, response_name: str, user_id: int, cooldown_duration: int
    ) -> bool:
        """Check if user is on cooldown for specific response"""
        cooldown_key = f"{response_name}_{user_id}"
        current_time = time.time()

        if cooldown_key in self.user_cooldowns:
            if current_time - self.user_cooldowns[cooldown_key] < cooldown_duration:
                return True

        self.user_cooldowns[cooldown_key] = current_time
        return False

    def format_response(self, response: str, message: discord.Message) -> str:
        """Format response with placeholders"""
        user = message.author
        guild = message.guild

        placeholders = {
            "user": user.display_name,
            "mention": user.mention,
            "username": user.name,
            "server": guild.name if guild else "DM",
            "channel": (getattr(message.channel, "name", None) or "DM"),
            "time": datetime.now().strftime("%H:%M"),
            "date": datetime.now().strftime("%d.%m.%Y"),
        }

        formatted_response = response
        for placeholder, value in placeholders.items():
            formatted_response = formatted_response.replace(
                f"{{{placeholder}}}", str(value)
            )

        return formatted_response

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel and isinstance(message.channel, (discord.TextChannel, discord.Thread)):
                content = (message.content or "").lower()
                spam_keywords = ["bro"]

                found_spam = any(k in content for k in spam_keywords)

                if not found_spam and getattr(message, "attachments", None):
                    for att in message.attachments:
                        fname = (att.filename or "").lower()
                        url = (att.url or "").lower()
                        if "1.jpg" in fname or "1.jpg" in url:
                            found_spam = True
                            break

                if not found_spam and getattr(message, "embeds", None):
                    for e in message.embeds:
                        img = getattr(e, "image", None)
                        if img and getattr(img, "url", None):
                            if "1.jpg" in img.url.lower():
                                found_spam = True
                                break

                if found_spam:
                    try:
                        await message.delete()
                    except Exception:
                        pass

                    dm_text = (
                        "Пожалуйста, выйдите из аккаунта и смените пароль, вас взломали!\n"
                        "Please log out of your account and change your password, you've been hacked!\n"
                    )
                    dm_sent = False
                    try:
                        await message.author.send(dm_text)
                        dm_sent = True
                    except Exception:
                        dm_sent = False

                    if not dm_sent:
                        try:
                            await message.channel.send(f"{message.author.mention} {dm_text}")
                        except Exception:
                            pass

                    return

        if not self.automatic_responses:
            return

        if (
            isinstance(message.channel, (discord.TextChannel, discord.Thread))
            and message.channel.category_id in config.IGNORED_CATEGORIES
        ):
            return

        message_content = message.content.lower()

        for response_name, response_data in self.automatic_responses.items():
            if not response_data.get("enabled", True):
                continue

            triggers = response_data.get("triggers", [])
            if not any(trigger.lower() in message_content for trigger in triggers):
                continue

            if not self.check_conditions(response_data, message):
                continue

            cooldown = response_data.get("conditions", {}).get("cooldown", 30)
            if self.check_cooldown(response_name, message.author.id, cooldown):
                continue

            responses = response_data.get("responses", [])
            if not responses:
                continue

            selected_response = random.choice(responses)
            formatted_response = self.format_response(selected_response, message)

            try:
                delete_trigger = response_data.get("conditions", {}).get(
                    "delete_trigger", False
                )
                if delete_trigger:
                    try:
                        await message.delete()
                    except:
                        pass

                await message.reply(formatted_response)

                logger.debug(
                    f"Automatic response '{response_name}' triggered by {message.author.id}"
                )
                break

            except discord.HTTPException as e:
                logger.error(f"Failed to send automatic response: {e}")

    @commands.slash_command(
        name="automatic_responses", description="Управление автоматическими ответами"
    )
    async def automatic_responses_cmd(self, ctx: discord.ApplicationContext):
        if not (isinstance(ctx.author, discord.Member) and is_staff(ctx.author)):
            embed = discord.Embed(
                title="❌ Доступ запрещен",
                description="Эта команда доступна только персоналу.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.defer()

        embed = discord.Embed(
            title="🧠 Автоматические Ответы",
            description="Система автоматических ответов",
            color=0x00FF88,
        )

        enabled_responses = [
            name
            for name, data in self.automatic_responses.items()
            if data.get("enabled", True)
        ]
        disabled_responses = [
            name
            for name, data in self.automatic_responses.items()
            if not data.get("enabled", True)
        ]

        embed.add_field(
            name="📊 Статистика",
            value=f"**Всего:** {len(self.automatic_responses)}\n**Включено:** {len(enabled_responses)}\n**Отключено:** {len(disabled_responses)}",
            inline=True,
        )

        if enabled_responses:
            embed.add_field(
                name="✅ Активные ответы",
                value=", ".join([f"`{name}`" for name in enabled_responses[:10]]),
                inline=False,
            )

        if disabled_responses:
            embed.add_field(
                name="❌ Отключенные ответы",
                value=", ".join([f"`{name}`" for name in disabled_responses[:10]]),
                inline=False,
            )

        embed.set_footer(text="Используйте команды управления для настройки")

        await ctx.followup.send(embed=embed)

    @commands.slash_command(
        name="toggle_automatic_response",
        description="Включить/выключить автоматический ответ",
    )
    async def toggle_automatic_response(
        self,
        ctx: discord.ApplicationContext,
        name: discord.Option(str, description="Название ответа для переключения"),  # type: ignore
    ):
        if ctx.author.id != config.ADMIN_USER_ID:
            embed = discord.Embed(
                title="❌ Доступ запрещен",
                description="Эта команда доступна только главному администратору.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.defer()

        if name not in self.automatic_responses:
            embed = discord.Embed(
                title="❌ Ответ не найден",
                description=f"Автоматический ответ `{name}` не существует.",
                color=0xFF4444,
            )
            available = ", ".join([f"`{n}`" for n in self.automatic_responses.keys()])
            if available:
                embed.add_field(name="Доступные ответы", value=available, inline=False)
            await ctx.followup.send(embed=embed, ephemeral=True)
            return

        old_status = self.automatic_responses[name].get("enabled", True)
        self.automatic_responses[name]["enabled"] = not old_status
        new_status = self.automatic_responses[name]["enabled"]

        if self.save_automatic_responses():
            embed = discord.Embed(
                title="🔄 Статус изменен",
                description=f"Автоматический ответ `{name}` {'включен' if new_status else 'отключен'}",
                color=0x00FF88 if new_status else 0xFF4444,
            )
            embed.add_field(
                name="Изменение статуса",
                value=f"{'❌ Отключен' if old_status else '✅ Включен'} → {'✅ Включен' if new_status else '❌ Отключен'}",
                inline=False,
            )
        else:
            embed = discord.Embed(
                title="❌ Ошибка сохранения",
                description="Не удалось сохранить изменения в файл.",
                color=0xFF4444,
            )

        await ctx.followup.send(embed=embed)

    @commands.slash_command(
        name="reload_automatic_responses",
        description="Перезагрузить автоматические ответы из файла",
    )
    async def reload_automatic_responses(self, ctx: discord.ApplicationContext):
        if ctx.author.id != config.ADMIN_USER_ID:
            embed = discord.Embed(
                title="❌ Доступ запрещен",
                description="Эта команда доступна только главному администратору.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.defer()

        old_count = len(self.automatic_responses)
        self.load_automatic_responses()
        new_count = len(self.automatic_responses)

        embed = discord.Embed(
            title="🔄 Автоматические ответы перезагружены",
            description="Конфигурация успешно обновлена из файла",
            color=0x00FF88,
        )
        embed.add_field(
            name="📊 Изменения",
            value=f"**До:** {old_count} ответов\n**После:** {new_count} ответов\n**Разница:** {new_count - old_count:+d}",
            inline=False,
        )
        embed.set_footer(text=f"Перезагружено {ctx.author}")

        await ctx.followup.send(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(AutomaticResponsesCog(bot))
