import os
import asyncio
from discord.ext import commands
import discord
import imageio_ffmpeg
import shutil
import subprocess

USER_ID = 505312523118182401
INTRO_PATH = os.path.abspath(os.path.join("assets", "intro", "intro1.wav"))
DEBOUNCE = 0.6
SETTLE = 0.4

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

    print("[VoiceIntro] Opus loaded:", discord.opus.is_loaded())
    try:
        if not discord.opus.is_loaded():
            discord.opus.load_opus("libopus.so.0")  # common on Linux
            print("[VoiceIntro] Opus loaded after load_opus:", discord.opus.is_loaded())
    except Exception as e:
        print("[VoiceIntro] Opus load failed:", repr(e))

    print("[VoiceIntro] ==========================")

_startup_debug()

class VoiceIntro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.is_running = False
        self.last_triggered = 0

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id != USER_ID:
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
            source = None
            try:
                channel = after.channel
                if channel is None:
                    return

                await asyncio.sleep(SETTLE)
                current = member.voice.channel if member.voice else None
                if current is None or current.id != channel.id:
                    return

                if member.guild.voice_client and member.guild.voice_client.is_connected():
                    return

                if not os.path.exists(INTRO_PATH):
                    print(f"Missing file: {INTRO_PATH}")
                    return

                print(f"[VoiceIntro] Attempting to join channel: {channel.name}")

                vc = await channel.connect()
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                source = discord.FFmpegPCMAudio(INTRO_PATH, executable=ffmpeg_exe, before_options="-nostdin -loglevel error", options="-vn", stderr=subprocess.PIPE)
                finished = asyncio.Event()

                def after_play(err):
                    print(f"Playback finished err={err}")
                    try:
                        if source and getattr(source, "stderr", None):
                            out = source.stderr.read().decode("utf-8", errors="replace").strip()
                            if out:
                                print("[VoiceIntro] ffmpeg stderr:\n" + out)
                    except Exception as e:
                        print("[VoiceIntro] Failed reading ffmpeg stderr:", repr(e))

                    finished.set()

                vc.play(source, after=after_play)
                await finished.wait()

            except Exception as e:
                print("[VoiceIntro] ERROR during intro:", repr(e))

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