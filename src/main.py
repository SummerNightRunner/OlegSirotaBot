from dotenv import load_dotenv
import discord
from discord.ext import commands

from src.config import load_config
from src.db.onboarding_store import OnboardingStore
from src.utils.logs import info, error
from src.views.enter_house import EnterHouseView

load_dotenv()
cfg = load_config()
store = OnboardingStore("data.sqlite3")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class Bot(commands.Bot):
    async def setup_hook(self):
        info("MAIN", "setup_hook_started")

        try:
            await self.store.init()
            info("MAIN", "store_initialized")
        except Exception as e:
            error("MAIN", "store_init_failed", err=repr(e))
            raise

        try:
            await self.load_extension("src.cogs.onboarding")
            info("MAIN", "extension_loaded", ext="src.cogs.onboarding")
        except Exception as e:
            error("MAIN", "extension_load_failed", ext="src.cogs.onboarding", err=repr(e))
            raise

        try:
            await self.load_extension("src.cogs.automod")
            info("MAIN", "extension_loaded", ext="src.cogs.automod")
        except Exception as e:
            error("MAIN", "extension_load_failed", ext="src.cogs.automod", err=repr(e))
            raise

        self.add_view(EnterHouseView(self.cfg, self.store))
        info("MAIN", "persistent_view_registered", view="EnterHouseView")


bot = Bot(command_prefix="!", intents=intents)
bot.cfg = cfg
bot.store = store


@bot.event
async def on_ready():
    info("MAIN", "bot_online", user=bot.user)


bot.run(bot.cfg.token)
