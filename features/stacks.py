from discord.ext import commands
from google.cloud.firestore_v1.types import StructuredAggregationQuery

from features.stack_repo import StackRepository
from features.stack_service import StackService
from features.stack_models import Stack
import re
from difflib import SequenceMatcher

repo = StackRepository()
service = StackService(repo)

def stack_type_label(size: int) -> str:
    if size == 2:
        return "Duo Stack"
    elif size == 3:
        return "Trio Stack"
    elif size == 5:
        return "Five Stack"
    return f"{size} Stack"

def render_stack(stk: Stack, role=None) -> str:
    role_ping = f"<@&{role.id}>" if role else ""
    stack_type = stack_type_label(stk.size)
    display_game_name = role.name if role else stk.game

    #template
    header = f"LF {role_ping} | **{display_game_name}** | **{stack_type}** | **{stk.time_text}**"
    filled = sum(1 for uid in stk.slots if uid is not None)
    slots_part = f"Code: `{stk.code}`  Slots: `{filled}/{stk.size}`  Host: {stk.slot_names[0] or 'Unknown'}"

    players = []
    for name in stk.slot_names:
        players.append(name if name else "empty")
    players_part = "Players: " + " • ".join(players)
    footer = f"Commands: `!join {stk.code}`, `!leave {stk.code}`"

    return "\n".join([header, slots_part, players_part, footer])

time12H_re = re.compile(r"^(0?[1-9]|1[0-2])([:.]([0-5][0-9]))?(am|pm)$", re.IGNORECASE)
time24H_re = re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$")

def valid_time(time_text: str) -> bool:
    timing = time_text.strip().lower().replace(" ", "")
    if time12H_re.match(timing):
        return True
    if time24H_re.match(timing):
        return True

    return False

def game_and_time(ctx, args, hint):
    if len(args) < 2:
        raise ValueError(f"Usage: `{hint}`")

    time_text = args[-1]
    game = " ".join(args[:-1])

    if not valid_time(time_text):
        raise ValueError("Invalid time format: Use `2am`, '9:30pm', '13:10'")

    return game, time_text

#for typo matching
def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def find_matching_role(guild, game_name: str):
    game_normal = game_name.lower().strip()

    best_role = None
    match_score = 0

    for role in guild.roles:
        role_normal = role.name.lower().strip()
        if game_normal in role_normal or role_normal in game_normal:
            return role

        score = similarity(game_normal, role_normal)
        if score > match_score:
            match_score = score
            best_role = role

    if match_score >= 0.65:
        return best_role

    return None

def setup(bot: commands.Bot):
    #use args and treat last word as time
    @bot.command()
    async def duo(ctx: commands.Context, *args):
        try:
            game, time_text = game_and_time(ctx, args, hint="!duo <game> <time>")
        except ValueError as e:
            await ctx.send(str(e))
            return

        matched_role = find_matching_role(ctx.guild, game)

        stk = Stack.create_stack(
            code=service.create_code(),
            size=2,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
        )
        repo.set(stk)
        await ctx.send(render_stack(stk, matched_role))

    @bot.command()
    async def trio(ctx: commands.Context, *args):
        try:
            game, time_text = game_and_time(ctx, args, hint="!trio <game> <time>")
        except ValueError as e:
            await ctx.send(str(e))
            return

        matched_role = find_matching_role(ctx.guild, game)

        stk = Stack.create_stack(
            code=service.create_code(),
            size=3,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
        )
        repo.set(stk)
        await ctx.send(render_stack(stk, matched_role))

    @bot.command()
    async def five_stack(ctx: commands.Context, *args):
        try:
            game, time_text = game_and_time(ctx, args, hint="!five <game> <time>")
        except ValueError as e:
            await ctx.send(str(e))
            return

        matched_role = find_matching_role(ctx.guild, game)

        stk = Stack.create_stack(
            code=service.create_code(),
            size=5,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
        )
        repo.set(stk)
        await ctx.send(render_stack(stk, matched_role))

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