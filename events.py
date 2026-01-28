from features.moderation import bad_word


async def on_ready(bot):
    print(f"Ready, {bot.user.name}")

async def on_message(bot, message):
    if message.author == bot.user:
        return

    if bad_word(message.content):
        await message.channel.send(f"{message.author.mention}, what a bully!")