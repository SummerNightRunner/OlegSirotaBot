import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict

from src.utils.logs import info, error


class AutoMod(commands.Cog):
    MAX_MESSAGES = 6
    WINDOW_SECONDS = 8
    STRIKE_WINDOW_MINUTES = 10
    TIMEOUT_MINUTES = 10
    LOOP_TIME_HOURS = 1

    def __init__(self, bot: commands.Bot, cfg):
        self.bot = bot
        self.cfg = cfg
        self._recent = defaultdict(deque)
        self._last_strike = {}
        try:
            self.cleanup_task.start()
            info("AUTOMOD", "cleanup_task_started", interval_hours=1)
        except Exception as e:
            error("AUTOMOD", "cleanup_task_start_failed", err=repr(e))
    
    def cog_unload(self):
        if self.cleanup_task.is_running():
            self.cleanup_task.cancel()
        info("AUTOMOD", "cleanup_task_stopped")

    @tasks.loop(hours=1)
    async def cleanup_task(self):
        now = datetime.now(timezone.utc)

        keys_to_delete = []
        removed_recent = 0
        removed_strikes = 0

        # переодическое удаление из _recent
        for key, values in self._recent.items():
            if (not values
                or now - values[-1] > timedelta(hours=self.LOOP_TIME_HOURS)):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._recent[key]
            removed_recent += 1
        keys_to_delete.clear()

        # переодическое удаление из _last_strike
        for key, value in self._last_strike.items():
            if now - value > timedelta(hours=self.LOOP_TIME_HOURS):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._last_strike[key]
            removed_strikes += 1
        keys_to_delete.clear()

        if removed_recent or removed_strikes:
            info("AUTOMOD", "cleanup_done", recent=removed_recent, strikes=removed_strikes)

    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        await self.bot.wait_until_ready()
        info("AUTOMOD", "cleanup_task_ready")

    @cleanup_task.error
    async def cleanup_task_error(self, exc: Exception):
        error("AUTOMOD", "cleanup_task_failed", err=repr(exc))

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

        def is_spam_msg(m: discord.Message) -> bool:
            return m.author.id == message.author.id and m.created_at >= cutoff
        
        # 5) проверка на спам
        if len(dq) > self.MAX_MESSAGES:
            # удаление сообщения
            try:
                deleted = await message.channel.purge(
                    limit=50,
                    check=is_spam_msg,
                    bulk=True
                )
                info("AUTOMOD", "spam_messages_deleted", guild=message.guild.id, channel=message.channel.id, user=message.author.id, count=len(deleted))
            except Exception as e:
                error("AUTOMOD", "delete_spam_failed", err=repr(e))
            dq.clear()
            self._recent.pop((message.guild.id, message.channel.id, message.author.id), None)

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
