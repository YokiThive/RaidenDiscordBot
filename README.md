# RaidenDiscordBot

## Overview
RaidenDiscordBot is a Discord bot built with Python. It includes voice intro playback, custom stack creation commands, Firebase-backed storage, and a configurable command prefix.
The goal of this project is to learn discord bot development, voice features, Firebase integration, and deployment using Render.

## App Features
- Voice intro playback when a specific user joins a voice channel
- Duo, trio, and five-stack creation
- Join and leave stack commands
- Firebase-backed stack storage
- Configurable server prefix
- Reminder-based stack expiration system

## Tech Stack
- Backend: Python
- Bot Framework: discord.py
- Database: Firebase Realtime Database
- Deployment: Render

## What I Learnt
- Building Discord bot features using `discord.py`
- Handling Discord voice connections and playback
- Integrating Firebase for persistent storage
- Managing command flow and user interactions
- Deploying and maintaining a bot on Render
- Debugging dependency and library compatibility issues

## What Could Be Improved
- Better logging instead of relying on `print()`
- More robust error handling around external services
- Admin or status commands for easier monitoring
- Better validation and message formatting for stack commands
- Add automated tests for core bot logic

## Setup
1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies
4. Create a `.env` file
5. Run the bot

## Installation
```bash
git clone https://github.com/<your-username>/RaidenDiscordBot.git
cd RaidenDiscordBot
python -m venv .venv
