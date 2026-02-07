import discord
from discord.ext import commands

from src.views.enter_house import EnterHouseView
from src.config import load_config

from src.db.onboarding_store import OnboardingStore

from src.utils.logs import info, warn, debug, error

class Onboarding(commands.Cog):
    def __init__(self, bot: commands.Bot, cfg, store: OnboardingStore):
        self.bot = bot
        self.cfg = cfg
        self.store = store

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != self.cfg.guild_id:
            return
        info("ONBOARDING", "member_join", guild=member.guild.id, user=member.id)

        role = member.guild.get_role(self.cfg.role_newborn_id)
        if role:
            await member.add_roles(role, reason="Onboarding")
            info("ONBOARDING", "added_newborn_role", guild=member.guild.id, user=member.id, role=role.id)

        ch = member.guild.get_channel(self.cfg.channel_first_words_id)
        if isinstance(ch, discord.TextChannel):
            try:
                msg = await ch.send(
                    f"{member.mention} Поздравляю тебя с твоим рождением, малыш.\n"
                    f"Напиши здесь свои первые слова, сынок, нажми кнопку ниже и тогда ты сможешь выйти к своим братьям.",
                    view=EnterHouseView(self.cfg, self.store),
                )
                try:
                    await self.store.mark_onboarding_state(member.guild.id, member.id, msg.id)
                    info("ONBOARDING", "saved_state", guild=member.guild.id, user=member.id, msg=msg.id)
                except Exception as e:
                    error("ONBOARDING", "store_onboarding_failed", err=repr(e))
            except Exception as e:
                error("ONBOARDING", "welcome_send_failed", err=repr(e))
        else:
            warn("ONBOARDING", "first_words_channel_invalid", guild=member.guild.id, channel=self.cfg.channel_first_words_id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 1) игнор ботов
        if message.author.bot:
            debug("ONBOARDING", "ignored_bot_message", user=message.author.id)
            return

        # 2) только наш сервер
        if message.guild is None or message.guild.id != self.cfg.guild_id:
            if message.guild is None:
                debug("ONBOARDING", "ignored_dm_message")
            else:
                debug("ONBOARDING", "ignored_other_guild", guild=message.guild.id, user=message.author.id)
            return

        # 3) интересует только канал "первые-слова"
        if message.channel.id != self.cfg.channel_first_words_id:
            debug(
                "ONBOARDING",
                "ignored_channel",
                guild=message.guild.id,
                user=message.author.id,
                channel=message.channel.id,
            )
            return

        # 4) отмечаем "первые слова" только для новорождённых
        newborn = message.guild.get_role(self.cfg.role_newborn_id)
        if newborn and newborn in message.author.roles:
            try:
                await self.store.mark_first_words(message.guild.id, message.author.id)
                info("ONBOARDING", "first_words", guild=message.guild.id, user=message.author.id, msg=message.id)
            except Exception as e:
                error("ONBOARDING", "mark_first_words_failed", err=repr(e))
        else:
            warn(
                "ONBOARDING",
                "not_newborn_on_message",
                guild=message.guild.id,
                user=message.author.id,
                role=self.cfg.role_newborn_id,
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != self.cfg.guild_id:
            return
        try:
            await self.store.delete_onboarding_state(member.guild.id, member.id)
            info("ONBOARDING", "delete_state", guild=member.guild.id, user=member.id)
        except Exception as e:
            error("ONBOARDING", "delete_onboarding_failed", err=repr(e))


async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot, bot.cfg, bot.store))
