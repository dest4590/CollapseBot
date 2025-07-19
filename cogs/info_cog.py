import time
from datetime import datetime

import discord
import requests
from discord.ext import commands
from loguru import logger

import config
from utils.helpers import get_emoji, get_uptime_string


class InfoCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(name="clients", description="Get list of clients")
    async def clients(self, ctx: discord.ApplicationContext):
        logger.debug(f"clients command executed")

        await ctx.defer()

        try:
            clients = requests.get(
                f"{config.API_BASE_URL}/clients",
                headers={"User-Agent": "CollapseBot"},
                timeout=10,
            ).json()
            fabric_clients = requests.get(
                f"{config.API_BASE_URL}/fabric_clients",
                headers={"User-Agent": "CollapseBot"},
                timeout=10,
            ).json()

            clients = clients + fabric_clients

            embed = discord.Embed(
                title=f"{get_emoji('clients', 1292469727125438575)} Client Library",
                color=0x5865F2,
                description=f"📊 **{len(clients)}** clients available",
            )

            regular_clients = [c for c in clients if not c.get("fabric", False)]
            fabric_clients_list = [c for c in clients if c.get("fabric", False)]

            if regular_clients:
                regular_list = "\n".join(
                    [
                        f"{'🔒' if not client['show_in_loader'] else '🟢'} **{client['name']}** `{client['version']}`"
                        for client in regular_clients
                    ]
                )
                embed.add_field(
                    name="Clients",
                    value=(
                        regular_list[:1024]
                        if len(regular_list) <= 1024
                        else regular_list[:1021] + "..."
                    ),
                    inline=False,
                )

            if fabric_clients_list:
                fabric_list = "\n".join(
                    [
                        f"{'🔒' if not client['show_in_loader'] else '🟢'} **{client['name']}** `{client['version']}`"
                        for client in fabric_clients_list
                    ]
                )
                embed.add_field(
                    name="Fabric Clients",
                    value=(
                        fabric_list[:1024]
                        if len(fabric_list) <= 1024
                        else fabric_list[:1021] + "..."
                    ),
                    inline=False,
                )

            embed.add_field(
                name="📝 Legend",
                value="🟢 Public • 🔒 Hidden",
                inline=False,
            )

            embed.set_footer(
                text=f"CollapseLoader • {len(clients)} total clients",
                icon_url=(
                    self.bot.user.avatar.url
                    if self.bot.user and self.bot.user.avatar
                    else None
                ),
            )

            await ctx.followup.send(embed=embed)

        except requests.RequestException as e:
            logger.error(f"Failed to fetch clients: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description="Failed to fetch client data. Please try again later.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @commands.slash_command(name="client", description="Get information about client")
    async def client_cmd(
        self,
        ctx: discord.ApplicationContext,
        client: discord.Option(str, description="Client to get information about"),  # type: ignore
    ):
        logger.debug(f"client command executed")

        await ctx.defer()

        try:
            clients = requests.get(
                f"{config.API_BASE_URL}/clients",
                headers={"User-Agent": "CollapseBot"},
                timeout=10,
            ).json()

            found_client = next(
                (c for c in clients if client.lower() in c["name"].lower()), None
            )

            if found_client:
                embed = discord.Embed(
                    title=f"🎯 {found_client['name']}",
                    color=0x00FF88 if found_client.get("working", False) else 0xFF4444,
                    description=f"{'✅ Working' if found_client.get('working', False) else '❌ Not Working'}",
                )

                embed.add_field(
                    name=f"{get_emoji('version', 1306166191177469952)} Version",
                    value=f"`{found_client['version']}`",
                    inline=True,
                )
                embed.add_field(
                    name=f"{get_emoji('file', 1306166288649027584)} Filename",
                    value=f"`{found_client['filename']}`",
                    inline=True,
                )
                embed.add_field(
                    name=f"{get_emoji('category', 1306166447399112744)} Category",
                    value=f"`{found_client['category']}`",
                    inline=True,
                )

                embed.add_field(
                    name=f"{get_emoji('main_class', 1306166348757598228)} Main Class",
                    value=f"`{found_client['main_class']}`",
                    inline=False,
                )

                status_indicators = []
                if found_client.get("working"):
                    status_indicators.append("✅ Working")
                if found_client.get("internal"):
                    status_indicators.append("🔒 Internal")
                if found_client.get("fabric"):
                    status_indicators.append("🧵 Fabric")
                if found_client.get("show_in_loader"):
                    status_indicators.append("👁️ Public")

                if status_indicators:
                    embed.add_field(
                        name="📊 Status",
                        value=" • ".join(status_indicators),
                        inline=False,
                    )

                try:
                    created_at = datetime.strptime(
                        found_client["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                except ValueError:
                    created_at = datetime.fromisoformat(
                        found_client["created_at"].replace("Z", "+00:00")
                    )

                try:
                    updated_at = datetime.strptime(
                        found_client["updated_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                except ValueError:
                    updated_at = datetime.fromisoformat(
                        found_client["updated_at"].replace("Z", "+00:00")
                    )

                embed.add_field(
                    name=f"{get_emoji('timeline', 1292468817234104401)} Created",
                    value=f"<t:{int(created_at.timestamp())}:R>",
                    inline=True,
                )
                embed.add_field(
                    name=f"{get_emoji('timeline', 1292468817234104401)} Updated",
                    value=f"<t:{int(updated_at.timestamp())}:R>",
                    inline=True,
                )

                embed.set_footer(
                    text="CollapseLoader Client Info",
                    icon_url=(
                        self.bot.user.avatar.url
                        if self.bot.user and self.bot.user.avatar
                        else None
                    ),
                )

                await ctx.followup.send(embed=embed)
            else:
                error_embed = discord.Embed(
                    title="❌ Client Not Found",
                    description=f"No client found matching `{client}`\n\nUse `/clients` to see all available clients.",
                    color=0xFF4444,
                )
                await ctx.followup.send(embed=error_embed, ephemeral=True)

        except requests.RequestException as e:
            logger.error(f"Failed to fetch client data: {e}")
            error_embed = discord.Embed(
                title="❌ Network Error",
                description="Failed to fetch client data. Please try again later.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @commands.slash_command(name="stats", description="Get CollapseLoader stats")
    async def stats(self, ctx: discord.ApplicationContext):
        logger.debug(f"stats command executed")

        await ctx.defer()

        try:
            from main import start_time

            analytics = requests.get(
                f"{config.API_BASE_URL}/counter",
                headers={"User-Agent": "CollapseBot"},
                timeout=10,
            ).json()

            endpoint_counts = {entry["endpoint"]: entry["count"] for entry in analytics}

            embed = discord.Embed(
                title="📊 CollapseLoader Statistics",
                color=0x5865F2,
                description="Real-time statistics and metrics",
            )

            embed.add_field(
                name="🤖 Bot Statistics",
                value=f"{get_emoji('servers', 1292468955490812007)} **{len(self.bot.guilds)}** servers\n"
                f"{get_emoji('users', 1292468955490812007)} **{sum(guild.member_count for guild in self.bot.guilds):,}** users\n"
                f"{get_emoji('ping', 1292468045662654568)} **{self.bot.latency * 1000:.1f}ms** ping\n"
                f"{get_emoji('timeline', 1292468817234104401)} **{get_uptime_string(start_time)}** uptime",
                inline=True,
            )

            embed.add_field(
                name="💾 System Statistics",
                value=(
                    f"{get_emoji('commands', 1292469546283958403)} **{len(self.bot.commands)}** commands\n"
                ),
                inline=True,
            )

            embed.add_field(
                name="📈 Usage Analytics",
                value=f"{get_emoji('analytics', 1292468265108635729)} **{endpoint_counts.get('api/analytics/start', '?'):,}** loader starts\n"
                f"{get_emoji('analytics', 1292468265108635729)} **{endpoint_counts.get('api/analytics/client', '?'):,}** client launches",
                inline=True,
            )

            embed.set_thumbnail(
                url=(
                    self.bot.user.avatar.url
                    if self.bot.user and self.bot.user.avatar
                    else None
                )
            )
            embed.set_footer(
                text="Live statistics • Updates every few minutes",
                icon_url=(
                    self.bot.user.avatar.url
                    if self.bot.user and self.bot.user.avatar
                    else None
                ),
            )

            await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description="Failed to fetch statistics. Please try again later.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @commands.slash_command(name="socials", description="Get CollapseLoader socials")
    async def socials(self, ctx: discord.ApplicationContext):
        logger.debug(f"socials command executed")

        embed = discord.Embed(
            title="🌐 CollapseLoader Social Links",
            color=0x1DA1F2,
            description="Connect with us on various platforms!",
        )

        embed.add_field(
            name="📱 Social Platforms",
            value="📱 [Telegram](https://t.me/collapseloader)\n"
            "💬 [Discord](https://discord.com/invite/FyKtnFqs6J)\n"
            "🌐 [Website](https://collapseloader.org)",
            inline=False,
        )

        embed.set_thumbnail(
            url=(
                self.bot.user.avatar.url
                if self.bot.user and self.bot.user.avatar
                else None
            )
        )
        embed.set_footer(text="Join our community!")

        await ctx.respond(embed=embed)

    @commands.slash_command(name="uptime", description="Get uptime of CollapseBot")
    async def uptime(self, ctx: discord.ApplicationContext):
        logger.debug(f"uptime command executed")

        from main import start_time

        uptime_seconds = int(time.time() - start_time)

        embed = discord.Embed(
            title="⏰ Bot Uptime",
            description=f"**{get_uptime_string(start_time)}**",
            color=0x00FF88,
        )

        embed.add_field(
            name="📊 Details",
            value=f"Started: <t:{int(start_time)}:R>\nTotal seconds: **{uptime_seconds:,}**",
            inline=False,
        )

        embed.set_footer(text="CollapseBot Status")

        await ctx.respond(embed=embed)

    @commands.slash_command(name="user", description="Get information about user")
    async def user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(discord.User, description="User to get information about"),  # type: ignore
    ):
        logger.debug(f"user command executed")

        if ctx.author.id != config.ADMIN_USER_ID:
            error_embed = discord.Embed(
                title="❌ Access Denied",
                description="This command is restricted to administrators.",
                color=0xFF4444,
            )
            await ctx.respond(embed=error_embed, ephemeral=True)
            return

        user_member = user if isinstance(user, discord.Member) else None

        embed = discord.Embed(
            title=f"👤 {user.display_name}",
            color=(
                user_member.color
                if user_member and user_member.color != discord.Color.default()
                else 0x5865F2
            ),
        )

        embed.add_field(
            name=f"{get_emoji('id', 1292470345755791360)} User ID",
            value=f"`{user.id}`",
            inline=True,
        )

        embed.add_field(
            name=f"{get_emoji('timeline', 1292468817234104401)} Account Created",
            value=f"<t:{int(user.created_at.timestamp())}:R>",
            inline=True,
        )

        embed.add_field(
            name=f"{get_emoji('timeline', 1292468817234104401)} Joined Server",
            value=(
                f"<t:{int(user_member.joined_at.timestamp())}:R>"
                if user_member and user_member.joined_at
                else "❌ Not in server"
            ),
            inline=True,
        )

        user_roles = user_member.roles if user_member else []
        if user_roles and ctx.guild and ctx.guild.default_role in user_roles:
            user_roles.remove(ctx.guild.default_role)

        if user_roles:
            role_mentions = [role.mention for role in user_roles[:10]]
            if len(user_roles) > 10:
                role_mentions.append(f"... and {len(user_roles) - 10} more")
            embed.add_field(
                name=f"{get_emoji('roles', 1292470773700755549)} Roles ({len(user_roles)})",
                value=" ".join(role_mentions) if role_mentions else "No roles",
                inline=False,
            )

        if hasattr(user, "status"):
            status_emoji = {
                "online": "🟢",
                "idle": "🟡",
                "dnd": "🔴",
                "offline": "⚫",
            }
            embed.add_field(
                name=f"{get_emoji('status', 1292471789628428409)} Status",
                value=f"{status_emoji.get(str(user.status), '❓')} {str(user.status).title()}",
                inline=True,
            )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text="User Information • Admin Only",
            icon_url=(
                self.bot.user.avatar.url
                if self.bot.user and self.bot.user.avatar
                else None
            ),
        )

        await ctx.respond(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(InfoCog(bot))
