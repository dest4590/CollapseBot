from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks
from loguru import logger

import config
from utils.helpers import is_staff


class VotingCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.voting_channel_id = 1352295334470225951
        self.vote_threshold = 10
        self.admin_role_ids = config.ADMIN_ROLES
        self.active_votes = {}
        self.check_votes.start()

    def cog_unload(self):
        self.check_votes.cancel()

    @tasks.loop(hours=1)
    async def check_votes(self):
        current_time = datetime.utcnow()

        for thread_id, data in list(self.active_votes.items()):
            if current_time >= data["end_time"]:
                try:
                    thread = self.bot.get_channel(thread_id)
                    if not isinstance(thread, discord.Thread):
                        continue

                    message = await thread.fetch_message(data["message_id"])
                    reactions = message.reactions

                    yes_votes = next(
                        (r.count - 1 for r in reactions if str(r.emoji) == "✅"), 0
                    )
                    no_votes = next(
                        (r.count - 1 for r in reactions if str(r.emoji) == "❌"), 0
                    )

                    if yes_votes >= self.vote_threshold:
                        admin_mentions = " ".join(
                            [f"<@&{role_id}>" for role_id in self.admin_role_ids]
                        )
                        embed = discord.Embed(
                            title="🔔 Результаты голосования",
                            description=f"Голосование за добавление клиента в {thread.mention} завершено с достаточной поддержкой!",
                            color=0x00FF88,
                        )
                        embed.add_field(
                            name="✅ Голосов за", value=str(yes_votes), inline=True
                        )
                        embed.add_field(
                            name="❌ Голосов против", value=str(no_votes), inline=True
                        )
                        embed.add_field(
                            name="Требуется действие",
                            value=f"{admin_mentions} пожалуйста, рассмотрите запрос на добавление клиента.",
                            inline=False,
                        )
                        await thread.send(embed=embed)

                    await thread.edit(archived=True)
                    del self.active_votes[thread_id]
                    logger.info(
                        f"Обработано голосование для ветки {thread_id}: {yes_votes} за, {no_votes} против"
                    )

                except discord.HTTPException as e:
                    logger.error(
                        f"Не удалось обработать голосование для ветки {thread_id}: {e}"
                    )

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if thread.parent_id != self.voting_channel_id:
            return

        try:
            embed = discord.Embed(
                title="🗳️ Голосование за добавление клиента",
                description="Проголосуйте, стоит ли добавить этого клиента в CollapseLoader.",
                color=0x5865F2,
            )
            embed.add_field(
                name="✅ За",
                value="Нажмите ✅, чтобы проголосовать за добавление",
                inline=False,
            )
            embed.add_field(
                name="❌ Против",
                value="Нажмите ❌, чтобы проголосовать против",
                inline=False,
            )
            embed.set_footer(text="Голосование завершится через 24 часа")

            message = await thread.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            self.active_votes[thread.id] = {
                "message_id": message.id,
                "end_time": datetime.utcnow() + timedelta(hours=24),
            }
            logger.info(f"Начато голосование в ветке {thread.id}")

        except discord.HTTPException as e:
            logger.error(f"Не удалось создать голосование в ветке {thread.id}: {e}")

    @commands.slash_command(
        name="vote_status", description="Проверить статус активных голосований"
    )
    async def vote_status(self, ctx: discord.ApplicationContext):
        if not (isinstance(ctx.author, discord.Member) and is_staff(ctx.author)):
            embed = discord.Embed(
                title="❌ Доступ запрещён",
                description="Эта команда доступна только персоналу.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.defer()

        if not self.active_votes:
            embed = discord.Embed(
                title="📊 Нет активных голосований",
                description="В настоящее время нет активных голосований за добавление клиентов.",
                color=0xFFAA00,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📊 Активные голосования",
            description=f"Текущие активные голосования за добавление клиентов: {len(self.active_votes)}",
            color=0x00FF88,
        )

        for thread_id, data in self.active_votes.items():
            thread = self.bot.get_channel(thread_id)
            if isinstance(thread, discord.Thread):
                time_left = data["end_time"] - datetime.utcnow()
                hours_left = time_left.total_seconds() / 3600
                embed.add_field(
                    name=f"Ветка: {thread.name}",
                    value=f"ID сообщения: {data['message_id']}\nОсталось времени: {hours_left:.1f} часов",
                    inline=False,
                )

        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(
        name="end_vote", description="Завершить голосование вручную"
    )
    async def end_vote(self, ctx: discord.ApplicationContext):
        if ctx.author.id != config.ADMIN_USER_ID:
            embed = discord.Embed(
                title="❌ Доступ запрещён",
                description="Эта команда доступна только главному администратору.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.defer()

        thread = ctx.channel
        if not isinstance(thread, discord.Thread):
            embed = discord.Embed(
                title="❌ Неверная ветка",
                description="Эту команду можно использовать только внутри ветки.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        thread_id = thread.id
        if thread_id not in self.active_votes:
            embed = discord.Embed(
                title="❌ Голосование не найдено",
                description="Активное голосование для этой ветки не найдено.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            del self.active_votes[thread_id]
            embed = discord.Embed(
                title="✅ Голосование завершено",
                description="Голосование в этой ветке было завершено вручную.",
                color=0x00FF88,
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Не удалось завершить голосование для ветки {thread_id}: {e}")
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Не удалось завершить голосование. Пожалуйста, попробуйте снова.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(VotingCog(bot))
