from dotenv import load_dotenv
import discord
from discord.ext import commands
from src.config import load_config
from src.db.onboarding_store import OnboardingStore
from src.views.enter_house import EnterHouseView

load_dotenv()
cfg = load_config()
store = OnboardingStore("data.sqlite3")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.cfg = cfg
bot.store = store

@bot.event
async def on_ready():
    print(f"🟢 Бот Онлайн: {bot.user}")

    await store.init()

    await bot.load_extension("src.cogs.onboarding")

    # регистрируем view с cfg
    bot.add_view(EnterHouseView(cfg, store))


bot.run(cfg.token)
