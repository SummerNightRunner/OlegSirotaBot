import discord
from discord.ext import commands

def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True  # пока оставим; позже можно убрать, если уйдём от !
    return commands.Bot(command_prefix="!", intents=intents)
