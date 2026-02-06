import discord
from discord.ext import commands

from src.views.enter_house import EnterHouseView
from src.config import load_config

from src.db.onboarding_store import OnboardingStore

class Onboarding(commands.Cog):
    def __init__(self, bot: commands.Bot, cfg, store: OnboardingStore):
        self.bot = bot
        self.cfg = cfg
        self.store = store

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != self.cfg.guild_id:
            return

        role = member.guild.get_role(self.cfg.role_newborn_id)
        if role:
            await member.add_roles(role, reason="Onboarding")

        ch = member.guild.get_channel(self.cfg.channel_first_words_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(
                    f"{member.mention} Поздравляю тебя с твоим рождением, малыш.\n"
                    f"Напиши здесь свои первые слова, сынок, нажми кнопку ниже и тогда ты сможешь выйти к своим братьям.",
                    view=EnterHouseView(self.cfg, self.store, target_user_id=member.id),
                )
            except Exception as e:
                print("WELCOME SEND FAILSED:", repr(e))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 1) игнор ботов
        if message.author.bot:
            return

        # 2) только наш сервер
        if message.guild is None or message.guild.id != self.cfg.guild_id:
            return

        # 3) интересует только канал "первые-слова"
        if message.channel.id != self.cfg.channel_first_words_id:
            return

        # 4) отмечаем "первые слова" только для новорождённых
        newborn = message.guild.get_role(self.cfg.role_newborn_id)
        if newborn and newborn in message.author.roles:
            await self.store.mark_first_words(message.guild.id, message.author.id)

async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot, bot.cfg, bot.store))
