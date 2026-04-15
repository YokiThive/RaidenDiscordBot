import os
import asyncio
from discord.ext import commands
import discord
import imageio_ffmpeg
import shutil

USER_ID = 505312523118182401
INTRO_PATH = os.path.abspath(os.path.join("assets", "intro", "intro1.wav"))

def _startup_debug():
    print("[VoiceIntro] ===== Startup Debug =====")
    print("[VoiceIntro] INTRO_PATH:", INTRO_PATH)
    print("[VoiceIntro] INTRO_PATH exists:", os.path.exists(INTRO_PATH))

    #PyNaCl check
    try:
        import nacl  # noqa: F401
        import nacl.utils
        print("[VoiceIntro] PyNaCl OK")
    except Exception as e:
        print("[VoiceIntro] PyNaCl MISSING/BROKEN:", repr(e))

    #system ffmpeg
    print("[VoiceIntro] ffmpeg in PATH:", shutil.which("ffmpeg"))

    #bundled ffmpeg
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        print("[VoiceIntro] imageio-ffmpeg exe:", ffmpeg_exe)
        print("[VoiceIntro] imageio-ffmpeg exe exists:", os.path.exists(ffmpeg_exe))
    except Exception as e:
        print("[VoiceIntro] imageio-ffmpeg ERROR:", repr(e))

    print("[VoiceIntro] ==========================")

_startup_debug()

class VoiceIntro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.last_played = 0
        self.is_running = False
        self.last_triggered = 0
        self.debounce = 0.6

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id != USER_ID:
            return

        if member.bot:
            return

        #triggers when join channel
        if after.channel is None:
            return

        if before.channel is not None:
            return

        now = asyncio.get_event_loop().time()
        if now - self.last_triggered < self.debounce:
            return
        self.last_triggered = now

        async with self.lock:
            if self.is_running:
                return
            self.is_running = True

            vc = None
            try:
                channel = after.channel
                if channel is None:
                    return

                await asyncio.sleep(0.4)
                current = member.voice.channel if member.voice else None
                if current is None or current.id != channel.id:
                    return

                existing_vc = member.guild.voice_client
                if existing_vc and existing_vc.is_connected():
                    return

                if not os.path.exists(INTRO_PATH):
                    print(f"Missing file: {INTRO_PATH}")
                    return

                print(f"[VoiceIntro] Attempting to join channel: {channel.name}")

                try:
                    vc = await channel.connect(reconnect=False)
                except Exception as e:
                    print(f"[VoiceIntro] Failed to connect to '{channel.name}' ({channel.id}): {type(e).__name__}: {e}")
                    return

                await asyncio.sleep(0.5)

                if not vc.is_connected():
                    print("[VoiceIntro] Voice client disconnected before playback started")
                    return

                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                source = discord.FFmpegPCMAudio(INTRO_PATH, executable=ffmpeg_exe)
                finished = asyncio.Event()

                def after_play(err):
                    print(f"Playback finished err={err}")
                    finished.set()

                try:
                    vc.play(source, after=after_play)
                except Exception as e:
                    print(f"[VoiceIntro] Failed to start playback: {type(e).__name__}: {e}")
                    return

                try:
                    await asyncio.wait_for(finished.wait(), timeout=10.0)
                    await asyncio.sleep(0.3)  # Small delay before disconnect
                except asyncio.TimeoutError:
                    print("[VoiceIntro] Playback timed out")

            finally:
                self.is_running = False
                try:
                    if vc and vc.is_connected():
                        await vc.disconnect()
                except Exception as e:
                    print(f"Failed to disconnect: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceIntro(bot))
    print("[VoiceIntro] Cog loaded")
