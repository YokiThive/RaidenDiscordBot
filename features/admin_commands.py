from discord.ext import commands
from features.prefix_repo import PrefixRepo

prefix_repo = PrefixRepo()

def setup(bot: commands.Bot):
    @bot.command()
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix(ctx: commands.Context, new_prefix: str = None):
        if new_prefix is None:
            current = prefix_repo.get(ctx.guild.id)
            await ctx.send(f"Current prefix is '{current}'")
            return

        new_prefix = new_prefix.strip()

        if len(new_prefix) > 3:
            await ctx.send("Prefix too long, make sure it is 3 characters or less")
            return

        if " " in new_prefix:
            await ctx.send("Prefix cannot contain spaces")
            return

        prefix_repo.set(ctx.guild.id, new_prefix)
        await ctx.send(f"Prefix updated to '{new_prefix}'")

    @prefix.error
    async def prefix_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need **Manage Server** permission to change the prefix")