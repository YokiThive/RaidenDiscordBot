from discord.ext import commands

def setup(bot: commands.Bot):
    @bot.command()
    async def hello(ctx):
        await ctx.send(f"Hello {ctx.author.mention}")

    @bot.command()
    async def ping(ctx):
        await ctx.send("pong")