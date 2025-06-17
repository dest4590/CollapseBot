from datetime import datetime
from typing import cast

import discord
import yaml
from discord.ext import commands
from loguru import logger

import config
from utils.helpers import is_staff


def get_snippets_list(_):
    """Get snippets list for autocomplete"""
    try:
        with open("snippets.yml", "r", encoding="utf-8") as file:
            snippets = yaml.safe_load(file) or {}
            return list(snippets.keys())
    except:
        return []


class AdminCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.snippets = {}
        self.load_snippets()

    def load_snippets(self):
        """Load snippets from YAML file"""
        try:
            with open("snippets.yml", "r", encoding="utf-8") as file:
                self.snippets = yaml.safe_load(file) or {}
                logger.info(f"✅ Loaded {len(self.snippets)} snippets")
        except FileNotFoundError:
            logger.warning("Snippets file not found, creating empty config")
            self.snippets = {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse snippets YAML: {e}")
            self.snippets = {}

    async def check_thread_permissions(self, ctx: discord.ApplicationContext) -> bool:
        """Check if user has permissions and command is in a thread"""
        if not (isinstance(ctx.author, discord.Member) and is_staff(ctx.author)):
            error_embed = discord.Embed(
                title="❌ Access Denied",
                description="You don't have permission to use this command.",
                color=0xFF4444,
            )
            error_embed.add_field(
                name="Required Permissions", value="Staff role required", inline=False
            )
            await ctx.respond(embed=error_embed, ephemeral=True)
            return False

        channel = self.bot.get_channel(ctx.channel_id)
        if not isinstance(channel, discord.Thread):
            error_embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in forum threads.",
                color=0xFF4444,
            )
            error_embed.add_field(
                name="💡 Tip",
                value="Navigate to a forum thread to use this command.",
                inline=False,
            )
            await ctx.respond(embed=error_embed, ephemeral=True)
            return False

        return True

    @commands.slash_command(name="close", description="Close forum thread")
    async def close(self, ctx: discord.ApplicationContext):
        if not await self.check_thread_permissions(ctx):
            return

        logger.debug(f"close command executed by {ctx.author.id}")

        await ctx.defer()

        channel = self.bot.get_channel(ctx.channel_id)
        thread = cast(discord.Thread, channel)

        try:
            original_name = thread.name
            new_name = original_name
            if len(new_name) > 70:
                new_name = new_name[:70]

            await thread.edit(name=f"{new_name} (CLOSED)", locked=True)

            embed = discord.Embed(
                title="🔒 Thread Closed",
                description="This thread has been successfully closed and locked.",
                color=0xFF4444,
            )
            embed.add_field(
                name="📝 Actions Taken",
                value="✅ Thread locked\n✅ Thread archived\n✅ Title updated",
                inline=False,
            )
            embed.add_field(name="👤 Closed by", value=ctx.author.mention, inline=True)
            embed.set_footer(
                text=f"Original title: {original_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.followup.send(embed=embed)
            await thread.archive()

        except discord.HTTPException as e:
            logger.error(f"Failed to close thread: {e}")
            error_embed = discord.Embed(
                title="❌ Failed to Close Thread",
                description="An error occurred while closing the thread.",
                color=0xFF4444,
            )
            error_embed.add_field(
                name="Possible Issues",
                value="• Missing bot permissions\n• Thread already locked\n• Discord API error",
                inline=False,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @commands.slash_command(name="fixed", description="Mark forum thread as fixed")
    async def fixed(self, ctx: discord.ApplicationContext):
        if not await self.check_thread_permissions(ctx):
            return

        logger.debug(f"fixed command executed by {ctx.author.id}")

        await ctx.defer()

        channel = self.bot.get_channel(ctx.channel_id)
        thread = cast(discord.Thread, channel)

        try:
            original_name = thread.name
            new_name = original_name
            if len(new_name) > 70:
                new_name = new_name[:70]

            await thread.edit(name=f"{new_name} (FIXED)")

            embed = discord.Embed(
                title="🔧 Thread Marked as Fixed",
                description="This issue has been resolved and marked as fixed.",
                color=0x00FF88,
            )
            embed.add_field(
                name="✅ Status Update",
                value="Thread marked as **FIXED**",
                inline=False,
            )
            embed.add_field(name="👤 Fixed by", value=ctx.author.mention, inline=True)
            embed.add_field(
                name="💡 Next Steps",
                value="Thread remains open for follow-up questions.",
                inline=True,
            )
            embed.set_footer(
                text=f"Original title: {original_name}",
                icon_url=ctx.author.display_avatar.url,
            )

            await ctx.followup.send(embed=embed)

        except discord.HTTPException as e:
            logger.error(f"Failed to mark thread as fixed: {e}")
            error_embed = discord.Embed(
                title="❌ Failed to Update Thread",
                description="Unable to mark thread as fixed.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @commands.slash_command(name="added", description="Mark forum thread as added")
    async def add(self, ctx: discord.ApplicationContext):
        if not await self.check_thread_permissions(ctx):
            return

        logger.debug(f"added command executed by {ctx.author.id}")

        await ctx.defer()

        channel = self.bot.get_channel(ctx.channel_id)
        thread = cast(discord.Thread, channel)

        try:
            original_name = thread.name
            new_name = original_name
            if len(new_name) > 70:
                new_name = new_name[:70]
            await thread.edit(name=f"{new_name} (ADDED)")

            embed = discord.Embed(
                title="➕ Client Added",
                description="The requested client has been added.",
                color=0x00D4AA,
            )
            embed.add_field(
                name="🎉 Status Update",
                value="Client request marked as **ADDED**",
                inline=False,
            )
            embed.add_field(name="👤 Added by", value=ctx.author.mention, inline=True)
            
            await ctx.followup.send(embed=embed)
            await thread.archive()

        except discord.HTTPException as e:
            logger.error(f"Failed to mark thread as added: {e}")
            error_embed = discord.Embed(
                title="❌ Failed to Update Thread",
                description="Unable to mark thread as added.",
                color=0xFF4444,
            )
            await ctx.followup.send(embed=error_embed, ephemeral=True)

    @commands.slash_command(name="lock", description="Lock and archive the thread")
    async def lock(self, ctx: discord.ApplicationContext):
        if not await self.check_thread_permissions(ctx):
            return

        logger.debug(f"lock command executed by {ctx.author.id}")

        channel = self.bot.get_channel(ctx.channel_id)
        thread = cast(discord.Thread, channel)

        embed = discord.Embed(
            title="🔒 Thread Locked",
            description="This thread has been locked and will be archived.",
            color=0xFF8800,
        )
        embed.add_field(name="👤 Locked by", value=ctx.author.mention, inline=True)
        embed.add_field(
            name="⏰ Locked at",
            value=f"<t:{int(datetime.utcnow().timestamp())}:R>",
            inline=True,
        )
        embed.set_footer(
            text="Thread is now read-only", icon_url=ctx.author.display_avatar.url
        )

        await ctx.respond(embed=embed)

        try:
            await thread.edit(locked=True)
            await thread.archive()
        except discord.HTTPException as e:
            logger.error(f"Failed to lock thread: {e}")

    @commands.slash_command(
        name="snippet", description="Send a predefined snippet response"
    )
    async def snippet(
        self,
        ctx: discord.ApplicationContext,
        name: discord.Option(str, description="Name of the snippet to send", autocomplete=discord.utils.basic_autocomplete(get_snippets_list)),  # type: ignore
    ):
        if not (isinstance(ctx.author, discord.Member) and is_staff(ctx.author)):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You don't have permission to use this command.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if name not in self.snippets:
            embed = discord.Embed(
                title="❌ Snippet Not Found",
                description=f"Snippet `{name}` doesn't exist.",
                color=0xFF4444,
            )
            available = ", ".join([f"`{s}`" for s in list(self.snippets.keys())[:10]])
            if available:
                embed.add_field(
                    name="Available snippets", value=available, inline=False
                )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        snippet = self.snippets[name]

        embed = discord.Embed(
            title=snippet.get("title", f"📋 {name.title()}"),
            description=snippet.get("content", "No content available"),
            color=snippet.get("color", 0x00FF88),
        )

        embed.set_footer(
            text=f"Snippet: {name} | Sent by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.respond(embed=embed)

        logger.info(f"Snippet '{name}' sent by {ctx.author.id} in {ctx.channel_id}")

    @commands.slash_command(name="snippets", description="List all available snippets")
    async def snippets_list(self, ctx: discord.ApplicationContext):
        if not (isinstance(ctx.author, discord.Member) and is_staff(ctx.author)):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You don't have permission to use this command.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if not self.snippets:
            embed = discord.Embed(
                title="📋 No Snippets Available",
                description="No snippets have been configured yet.",
                color=0xFFAA00,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Available Snippets",
            description="Here are all the available snippet commands:",
            color=0x00FF88,
        )

        snippet_list = []
        for snippet_name, snippet_data in self.snippets.items():
            title = snippet_data.get("title", snippet_name.title())
            snippet_list.append(f"`{snippet_name}` - {title}")

        chunk_size = 10
        chunks = [
            snippet_list[i : i + chunk_size]
            for i in range(0, len(snippet_list), chunk_size)
        ]

        for i, chunk in enumerate(chunks):
            field_name = "Snippets" if i == 0 else f"Snippets (continued {i+1})"
            embed.add_field(name=field_name, value="\n".join(chunk), inline=False)

        embed.set_footer(text="Use /snippet <name> to send a snippet")
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(
        name="reload_snippets", description="Reload snippets from file"
    )
    async def reload_snippets(self, ctx: discord.ApplicationContext):
        if ctx.author.id != config.ADMIN_USER_ID:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="This command is only available to the main administrator.",
                color=0xFF4444,
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.defer()
        old_count = len(self.snippets)
        self.load_snippets()
        new_count = len(self.snippets)

        embed = discord.Embed(
            title="🔄 Snippets Reloaded",
            description="Snippet configuration has been successfully updated from file",
            color=0x00FF88,
        )
        embed.add_field(
            name="📊 Changes",
            value=f"**Before:** {old_count} snippets\n**After:** {new_count} snippets\n**Difference:** {new_count - old_count:+d}",
            inline=False,
        )
        embed.set_footer(text=f"Reloaded by {ctx.author}")

        await ctx.followup.send(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(AdminCog(bot))
