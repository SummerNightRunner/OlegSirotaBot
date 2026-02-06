import discord
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="warn", description="Выдать предупреждение участнику")
    @app_commands.describe(member="Кому выдать", reason="Причина предупреждения")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        # здесь позже добавим запись в БД
        await interaction.response.send_message(
            f"{member.mention} предупреждение. Причина: {reason}",
            ephemeral=False
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
