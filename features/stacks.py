from discord.ext import commands, tasks
from google.cloud.firestore_v1.types import StructuredAggregationQuery

from features.stack_repo import StackRepository
from features.stack_service import StackService
from features.stack_models import Stack
from features.prefix_repo import PrefixRepo
import re
from difflib import SequenceMatcher

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time as t
import random

prefix_repo = PrefixRepo()
repo = StackRepository()
service = StackService(repo)
timezone = ZoneInfo("Asia/Kuala_Lumpur")
success_messages = ["Come. n o w.",
                    "Where?",
                    "It's time to underperform and transform! *transformer noises*",
                    "Come heeeeeeeeeeeeeeeeeeeere!",
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARGH!!!"]

sad_messages = ["Not enough players, stack expired",
                "Nobody showed up, deleting the stack",
                "Nobody wants to play with you, give up"]

def stack_type_label(size: int) -> str:
    if size == 2:
        return "Duo Stack"
    elif size == 3:
        return "Trio Stack"
    elif size == 5:
        return "Five Stack"
    return f"{size} Stack"

def render_stack_create(stk: Stack, role=None, prefix: str = "!") -> str:
    role_ping = f"<@&{role.id}>" if role else ""
    stack_type = stack_type_label(stk.size)
    display_game_name = role.name if role else stk.game

    #template
    header = f"LF {role_ping} | **{display_game_name}** | **{stack_type}** | **{stk.time_text}**"
    filled = sum(1 for uid in stk.slots if uid is not None)
    slots_part = f"Slots: `{filled}/{stk.size}`  Host: {stk.slot_names[0] or 'Unknown'}"

    players = [(name if name else "empty") for name in stk.slot_names]
    players_part = "Players: " + " • ".join(players)
    footer = f"Commands: `{prefix}join {stk.code}`, `{prefix}leave {stk.code}`"

    return "\n".join([header, slots_part, players_part, footer])

def render_stack_status(stk: Stack, prefix: str = "!") -> str:
    filled = sum(1 for uid in stk.slots if uid is not None)
    slots_part = f"Slots: `{filled}/{stk.size}`  Host: {stk.slot_names[0] or 'Unknown'}"

    players = [(name if name else "empty") for name in stk.slot_names]
    players_part = "Players: " + " • ".join(players)
    footer = f"Commands: `{prefix}join {stk.code}`, `{prefix}leave {stk.code}`"

    return "\n".join([slots_part, players_part, footer])

time12H_re = re.compile(r"^(0?[1-9]|1[0-2])([:.]([0-5][0-9]))?(am|pm)$", re.IGNORECASE)
time24H_re = re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$")

def time_to_remind_at(time_text: str) -> int:
    time_to_remind = time_text.strip().lower().replace(" ", "")
    now = datetime.now(timezone)

    t12 = time12H_re.match(time_to_remind)
    if t12:
        hour = int(t12.group(1))
        minute = int(t12.group(3) or "0")
        amnpm = t12.group(4).lower()

        if amnpm == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12

        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)

        return int(target_time.timestamp())

    t24 = time24H_re.match(time_to_remind)
    if t24:
        hour = int(t24.group(1))
        minute = int(t24.group(2))

        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)

        return int(target_time.timestamp())

    raise ValueError(f"Invalid time format")

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
    @tasks.loop(seconds=20)
    async def reminder_loop():
        now = int(t.time())
        stacks = repo.list()
        if not stacks:
            return

        for code, stk in stacks.items():
            reminder = int(stk.reminder or 0)
            channel_id = int(stk.channel_id or 0)

            if reminder <= 0 or channel_id <= 0:
                continue

            if now < reminder:
                continue

            channel = bot.get_channel(channel_id)

            if channel is None:
                try:
                    channel = await bot.fetch_channel(channel_id)
                except Exception:
                    repo.delete(code)
                    continue

            try:
                if stk.is_full():
                    mentions = " ".join(f"<@{uid}>" for uid in stk.member_ids())
                    await channel.send(f"{mentions}\n {random.choice(success_messages)} (**{stk.game}** | **{stk.time_text}**)")
                else:
                    filled = sum(1 for uid in stk.slots if uid is not None)
                    await channel.send(f"{random.choice(sad_messages)}\n"
                                       f"(**{stk.game}** | **{stk.time_text}** | Slots: `{filled}/{stk.size}`)")
            finally:
                repo.delete(code)

    @reminder_loop.before_loop
    async def before_loop():
        await bot.wait_until_ready()

    async def start_reminder():
        if not reminder_loop.is_running():
            reminder_loop.start()

    bot.add_listener(start_reminder, "on_ready")

    #use args and treat last word as time
    @bot.command()
    async def duo(ctx: commands.Context, *args):
        try:
            game, time_text = game_and_time(ctx, args, hint=f"{ctx.prefix}duo <game> <time>")
        except ValueError as e:
            await ctx.send(str(e))
            return

        matched_role = find_matching_role(ctx.guild, game)
        if matched_role:
            game = matched_role.name
        reminder = time_to_remind_at(time_text)

        stk = Stack.create_stack(
            code=service.create_code(),
            size=2,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
            channel_id=ctx.channel.id,
            reminder=reminder,
        )
        repo.set(stk)
        await ctx.send(render_stack_create(stk, matched_role, prefix=ctx.prefix))

    @bot.command()
    async def trio(ctx: commands.Context, *args):
        try:
            game, time_text = game_and_time(ctx, args, hint=f"{ctx.prefix}trio <game> <time>")
        except ValueError as e:
            await ctx.send(str(e))
            return

        matched_role = find_matching_role(ctx.guild, game)
        if matched_role:
            game = matched_role.name
        reminder = time_to_remind_at(time_text)

        stk = Stack.create_stack(
            code=service.create_code(),
            size=3,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
            channel_id=ctx.channel.id,
            reminder=reminder,
        )
        repo.set(stk)
        await ctx.send(render_stack_create(stk, matched_role, prefix=ctx.prefix))

    @bot.command()
    async def five_stack(ctx: commands.Context, *args):
        try:
            game, time_text = game_and_time(ctx, args, hint=f"{ctx.prefix}five_stack <game> <time>")
        except ValueError as e:
            await ctx.send(str(e))
            return

        matched_role = find_matching_role(ctx.guild, game)
        if matched_role:
            game = matched_role.name
        reminder = time_to_remind_at(time_text)

        stk = Stack.create_stack(
            code=service.create_code(),
            size=5,
            game=game,
            time_text=time_text,
            id=ctx.author.id,
            name=ctx.author.display_name,
            channel_id=ctx.channel.id,
            reminder=reminder,
        )
        repo.set(stk)
        await ctx.send(render_stack_create(stk, matched_role, prefix=ctx.prefix))

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
        await ctx.send(f"Joined successfully\n{render_stack_status(stk, prefix=ctx.prefix)}")

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

        if result.action == "left" and result.stack:
            await ctx.send(
                f"{result.message}\n{render_stack_status(result.stack, prefix=ctx.prefix)}")
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