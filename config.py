import os
import logging
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

def setup_logging():
    return logging.FileHandler(filename="discord.log",encoding="utf-8",mode="w")