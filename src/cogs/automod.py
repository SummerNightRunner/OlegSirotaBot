import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict

from src.utils.logs import info, error


class AutoMod(commands.Cog):
    MAX_MESSAGES = 6
    WINDOW_SECONDS = 8
    STRIKE_WINDOW_MINUTES = 10
    TIMEOUT_MINUTES = 10

    def __init__(self, bot: commands.Bot, cfg):
        self.bot = bot
        self.cfg = cfg
        self._recent = defaultdict(deque)
        self._last_strike = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 0) игнор ботов
        if message.author.bot:
            return
        
        # 1) только наш сервер
        if message.guild is None or message.guild.id != self.cfg.guild_id:
            return

        # 2) игнор модов и админов
        if message.author.guild_permissions.manage_messages:
            return
        
        # 3) сбор времени сообщений
        dq = self._recent[(message.guild.id, message.channel.id, message.author.id)]
        now = datetime.now(timezone.utc)
        dq.append(now)

        # 4) удаление сообщений вне окна спама
        cutoff = now - timedelta(seconds=self.WINDOW_SECONDS)
        while dq and dq[0] < cutoff:
             dq.popleft()
        if not dq:
            del self._recent[(message.guild.id, message.channel.id, message.author.id)]
        
        # 5) проверка на спам
        if len(dq) > self.MAX_MESSAGES:
            # удаление сообщения
            try:
                await message.delete()
                info("AUTOMOD", "spam_detected", guild=message.guild.id, channel=message.channel.id, user=message.author.id)
            except Exception as e:
                error("AUTOMOD", "delete_spam_failed", err=repr(e))
            dq.clear()

            last = self._last_strike.get((message.guild.id, message.author.id))
            self._last_strike[(message.guild.id, message.author.id)] = now

            if last and now - last <= timedelta(minutes=self.STRIKE_WINDOW_MINUTES):
                # мут
                until = now + timedelta(minutes=self.TIMEOUT_MINUTES)
                try:
                    await message.author.timeout(until, reason="AutoMod: spam")
                    info("AUTOMOD", "member_muted", guild=message.guild.id, user=message.author.id)
                    try:
                        await message.channel.send(
                            f"{message.author.mention} - этот сын отправился молчать в комнату к бабуле на 10 минут.",
                            delete_after=10
                        )
                        info("AUTOMOD", "mute_message_sent", guild=message.guild.id, channel=message.channel.id, user=message.author.id)
                    except Exception as e:
                        error("AUTOMOD", "mute_message_sending_failed", err=repr(e))
                except Exception as e:
                    error("AUTOMOD", "mute_failed", err=repr(e))
            else:
                # предупреждение
                try:
                    await message.channel.send(
                        f"{message.author.mention}, сынок, не спеши. Пиши спокойнее, за повтор пойдешь полчать в комнату к бабуле на 10 минут.",
                        delete_after=10
                    )
                    info("AUTOMOD", "warn_message_sent", guild=message.guild.id, channel=message.channel.id, user=message.author.id)
                except Exception as e:
                    error("AUTOMOD", "warn_message_sending_failed", err=repr(e))

            return

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot, bot.cfg))