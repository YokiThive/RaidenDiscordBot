import discord
from discord.ext import commands
import logging

import threading
from flask import Flask
import os

from config import DISCORD_TOKEN, setup_logging
import events
from features import basic_commands
from features import admin_commands

from features import stacks
from features.prefix_repo import PrefixRepo

prefix_repo = PrefixRepo()

async def get_prefix(bot, message):
    if message.guild is None:
        return PrefixRepo.DEFAULT
    return prefix_repo.get(message.guild.id)

def start_server():
    app = Flask(__name__)

    @app.get("/")
    def home():
        return "ok", 200

    @app.get("/health")
    def health():
        return "healthy", 200

    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()

    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN missing")

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True

    class Bot(commands.Bot):
        async def setup_hook(self):
            await self.load_extension("features.voice_intro")

    bot = Bot(command_prefix=get_prefix, intents=intents)

    # all my commands
    basic_commands.setup(bot)
    stacks.setup(bot)
    admin_commands.setup(bot)

    @bot.event
    async def on_ready():
        await events.on_ready(bot)

    @bot.event
    async def on_message(message):
        await events.on_message(bot, message)
        await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx, error):
        await ctx.send(f"Command Error: {error}")
        raise error

    handler = setup_logging()

    bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)