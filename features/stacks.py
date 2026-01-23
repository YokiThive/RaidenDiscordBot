from discord.ext import commands
from features.stack_repo import StackRepository
from features.stack_service import StackService
from features.stack_models import Stack

repo = StackRepository()
service = StackService(repo)

def render_stack(stk: Stack) -> str:
    return stk.toString()

def setup(bot: commands.Bot):
    @bot.command()
    async def duo(ctx: commands.Context, game: str, time_text: str):
        stk = Stack.create_stack(
            code=service.create_code(),
            size=2,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
        )
        repo.set(stk)
        await ctx.send(render_stack(stk))

    @bot.command()
    async def trio(ctx: commands.Context, game: str, time_text: str):
        stk = Stack.create_stack(
            code=service.create_code(),
            size=3,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
        )
        repo.set(stk)
        await ctx.send(render_stack(stk))

    @bot.command()
    async def five_stack(ctx: commands.Context, game: str, time_text: str):
        stk = Stack.create_stack(
            code=service.create_code(),
            size=5,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
        )
        repo.set(stk)
        await ctx.send(render_stack(stk))

    @bot.command()
    async def join(ctx: commands.Context, code: str):
        code = code.strip()
        stk = repo.get(code)

        if not stk:
            await ctx.send("Invalid code")
            return

        if stk.has_user(ctx.author.id):
            await ctx.send("You are already in this stack")
            return

        if stk.is_full():
            await ctx.send("Stack is full")
            return

        ok = stk.add_user(ctx.author.id, ctx.author.display_name)
        if not ok:
            await ctx.send("Could not join")
            return

        repo.set(stk)
        await ctx.send("Joined successfully \n" + render_stack(stk))

    @bot.command()
    async def leave(ctx: commands.Context, code: str):
        result = service.leave_stack(code, ctx.author.id)

        if not result.ok:
            await ctx.send(result.message)
            return

        if result.action == "deleted" and result.ping_ids:
            pings = ", ".join(f"<@{uid}>" for uid in result.ping_ids)
            await ctx.send(f"{pings}\nYour host left you in the dirt")
            return

        await ctx.send(result.message)

    @bot.command()
    async def stacks_list(ctx: commands.Context):
        stacks = repo.list()
        if not stacks:
            await ctx.send("No active stacks")
            return

        lines = []
        for code, stk in stacks.items():
            host = stk.slot_names[0] or "Unknonw"
            lines.append(f"`{code}` {stk.size}-stack {stk.game} Host: {host}")

        await ctx.send("Active stacks\n" + "\n".join(lines))