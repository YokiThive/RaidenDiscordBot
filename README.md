# RaidenDiscordBot

## Overview
RaidenDiscordBot is a Discord bot built with Python. It includes voice intro playback, custom stack creation commands, Firebase-backed storage, and a configurable command prefix.

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

## Setup
1. Clone the repository
3. Install dependencies
4. Create a `.env` file
5. Run the bot

## Installation
```bash
git clone https://github.com/YokiThive/RaidenDiscordBot.git
cd RaidenDiscordBot
python -m venv .venv
