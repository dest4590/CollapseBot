import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import discord
import requests
from discord.ext import commands
from loguru import logger

import config
from utils.helpers import get_emoji, get_uptime_string


@dataclass
class Client:
    """Client data structure matching API response."""
    id: int
    name: str
    version: str
    filename: str
    md5_hash: str
    size: int
    main_class: str
    show: bool
    working: bool
    launches: int
    downloads: int
    client_type: str
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "Client":
        """Create Client instance from dictionary."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            version=data.get("version", ""),
            filename=data.get("filename", ""),
            md5_hash=data.get("md5_hash", ""),
            size=data.get("size", 0),
            main_class=data.get("main_class", ""),
            show=data.get("show", False),
            working=data.get("working", False),
            launches=data.get("launches", 0),
            downloads=data.get("downloads", 0),
            client_type=data.get("client_type", "default"),
            created_at=data.get("created_at", ""),
        )


class InfoCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    def _fetch_clients(self, endpoint: str = "clients") -> Optional[List[Client]]:
        """Fetch and parse clients from the API endpoint."""
        try:
            response = requests.get(
                f"{config.API_BASE_URL}/{endpoint}",
                headers={"User-Agent": "CollapseBot"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict) and "data" in data:
                clients_data = data["data"]
            elif isinstance(data, list):
                clients_data = data
            else:
                logger.error(f"Unexpected API response format: {type(data)}")
                return None
            
            return [Client.from_dict(client) for client in clients_data]
        except requests.RequestException as e:
            logger.error(f"Failed to fetch clients from {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing client data: {e}")
            return None

    def _create_clients_embed(self, clients: List[Client], title: str, emoji: str = "clients") -> discord.Embed:
        """Create an embed for displaying clients list."""
        embed = discord.Embed(
            title=f"{get_emoji(emoji, 1292469727125438575)} {title}",
            color=0x5865F2,
            description=f"📊 **{len(clients)}** clients available",
        )

        if clients:
            regular_list = "\n".join(
                [
                    f"{'🔒' if not client.show else '🟢'} **{client.name}** `{client.version}`"
                    for client in clients
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

        return embed

    @commands.slash_command(name="clients", description="Get list of all clients")
    async def clients(self, ctx: discord.ApplicationContext):
        logger.debug(f"clients command executed")
        await ctx.defer()

        clients = self._fetch_clients("clients")
        if clients is None:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Failed to fetch client data. Please try again later.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)
            return

        embed = self._create_clients_embed(clients, "Client Library")
        await ctx.followup.send(embed=embed)

    @commands.slash_command(name="fabric-clients", description="Get list of Fabric clients")
    async def fabric_clients(self, ctx: discord.ApplicationContext):
        logger.debug(f"fabric-clients command executed")
        await ctx.defer()

        clients = self._fetch_clients("fabric-clients")
        if clients is None:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Failed to fetch Fabric client data. Please try again later.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)
            return

        embed = self._create_clients_embed(clients, "Fabric Client Library", "clients")
        await ctx.followup.send(embed=embed)

    @commands.slash_command(name="forge-clients", description="Get list of Forge clients")
    async def forge_clients(self, ctx: discord.ApplicationContext):
        logger.debug(f"forge-clients command executed")
        await ctx.defer()

        clients = self._fetch_clients("forge-clients")
        if clients is None:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Failed to fetch Forge client data. Please try again later.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)
            return

        embed = self._create_clients_embed(clients, "Forge Client Library", "clients")
        await ctx.followup.send(embed=embed)

    def get_clients(self):
        """Fetch the list of clients from the API."""
        return config.CLIENTS

    @commands.slash_command(name="client", description="Get information about client")
    async def client_cmd(
        self,
        ctx: discord.ApplicationContext,
        client: discord.Option(str, description="Client to get information about", autocomplete=discord.utils.basic_autocomplete(get_clients)), # type: ignore
    ):
        logger.debug(f"client command executed")
        await ctx.defer()

        clients = self._fetch_clients("clients")
        if clients is None:
            error_embed = discord.Embed(
                title="❌ Network Error",
                description="Failed to fetch client data. Please try again later.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)
            return

        found_client = next(
            (
                c
                for c in clients
                if client.lower() in c.name.lower()
                or client.lower() in c.filename.lower()
            ),
            None,
        )

        if found_client:
            embed = discord.Embed(
                title=found_client.name,
                color=0x00FF88 if found_client.working else 0xFF4444,
                description=f"{'✅ Working' if found_client.working else '❌ Not Working'}",
            )

            embed.add_field(
                name=f"{get_emoji('version', 1306166191177469952)} Version",
                value=f"`{found_client.version}`",
                inline=True,
            )

            embed.add_field(
                name=f"{get_emoji('file', 1306166288649027584)} Filename",
                value=f"`{found_client.filename}`",
                inline=True,
            )

            embed.add_field(
                name=f"{get_emoji('main_class', 1306166348757598228)} Main Class",
                value=f"`{found_client.main_class}`",
                inline=False,
            )

            status_indicators = []
            if found_client.working:
                status_indicators.append("✅ Working")
            if found_client.show:
                status_indicators.append("👁️ Public")

            if status_indicators:
                embed.add_field(
                    name="📊 Status",
                    value=" • ".join(status_indicators),
                    inline=False,
                )

            type_emoji = {
                "fabric": "🧵",
                "forge": "🔨",
                "default": "📦"
            }
            embed.add_field(
                name="📦 Client Type",
                value=f"{type_emoji.get(found_client.client_type, '📦')} {found_client.client_type.title()}",
                inline=True,
            )

            embed.add_field(
                name="📊 Statistics",
                value=f"⬇️ **{found_client.downloads:,}** downloads\n🚀 **{found_client.launches:,}** launches",
                inline=True,
            )

            try:
                created_at = datetime.strptime(
                    found_client.created_at, "%Y-%m-%dT%H:%M:%S.%fZ"
                )
            except ValueError:
                created_at = datetime.fromisoformat(
                    found_client.created_at.replace("Z", "+00:00")
                )

            embed.add_field(
                name=f"{get_emoji('timeline', 1292468817234104401)} Created",
                value=f"<t:{int(created_at.timestamp())}:R>",
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

    @commands.slash_command(name="stats", description="Get CollapseLoader stats")
    async def stats(self, ctx: discord.ApplicationContext):
        logger.debug(f"stats command executed")

        await ctx.defer()

        try:
            from main import start_time

            analytics = requests.get(
                f"{config.API_BASE_URL}/api/statistics",
                headers={"User-Agent": "CollapseBot"},
                timeout=10,
            ).json()

            total_loader_launches = analytics.get("total_loader_launches", 0)
            total_client_downloads = analytics.get("total_client_downloads", 0)
            total_client_launches = analytics.get("total_client_launches", 0)

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
                value=f"{get_emoji('analytics', 1292468265108635729)} **{total_loader_launches}** loader starts\n"
                f"{get_emoji('analytics', 1292468265108635729)} **{total_client_downloads}** client downloads\n"
                f"{get_emoji('analytics', 1292468265108635729)} **{total_client_launches}** client launches",
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
