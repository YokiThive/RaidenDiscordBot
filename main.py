import discord
from discord.ext import commands
import logging
import sys
import time
import traceback

import threading
from flask import Flask
import os

from google.api_core.exceptions import exception_class_for_grpc_status

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

def retry_bot(bot, handler):
    retry_delay = 300
    max_delay = 3600
    current_attempt = 0
    max_attempts = 5

    while current_attempt < max_attempts:
        try:
            print(f"Attempt #{current_attempt + 1}")
            bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.INFO)
            break

        except discord.errors.HTTPException as e:
            if e.status == 429: #limit
                current_attempt += 1
                if current_attempt >= max_attempts:
                    sys.exit(1)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
            else:
                print(f"HTTP error: {e}")
                raise

        except Exception as e:
            print(f"Error: {e}")
            raise

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
        if isinstance(error, commands.CommandNotFound):
            return
        await ctx.send(f"Command Error: {error}")
        print(f"Command Error: {error}")

    @bot.event
    async def on_error(event, *args, **kwargs):
        error = sys.exc_info()
        if error[0] is discord.errors.HTTPException:
            if error[1].status == 429:
                print(f"Rate limit exceeded during {event}")
        traceback.print_exception(*error)

    handler = setup_logging()
    retry_bot(bot, handler)

    #bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)