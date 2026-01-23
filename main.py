import discord
from discord.ext import commands
import logging

from config import DISCORD_TOKEN, setup_logging
import events
from features import basic_commands

from features import stacks

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

#all my commands
basic_commands.setup(bot)
stacks.setup(bot)

@bot.event
async def on_ready():
    await events.on_ready(bot)

@bot.event
async def on_message(message):
    await events.on_message(bot, message)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Command Error: {error}")
    raise error

handler = setup_logging()

bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)