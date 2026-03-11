import os
import asyncio
import discord
# from discord import app_commands - allegedly unneeded.
from dotenv import load_dotenv
import traceback


from datetime import datetime

def build_status():
    """
    Centralized system status report.
    Later this will pull real telemetry.
    """

    # placeholders until wired to real telemetry
    glucose = "unknown"
    slope = "unknown"
    protocol_state = "idle"

    honey_ready = True
    kibble_ready = True

    return (
        "BCS STATUS\n\n"
        f"glucose: {glucose}\n"
        f"slope: {slope}\n"
        f"protocol: {protocol_state}\n\n"
        f"honey driver: {'ready' if honey_ready else 'busy'}\n"
        f"kibble driver: {'ready' if kibble_ready else 'busy'}\n"
        f"time: {datetime.utcnow().isoformat()}Z"
    )


# ---- load env ----
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")



if not BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN not set")

# ---- import hardware action ----
from bennycaresystem.drivers.servo_util import servo_rotate_once
from bennycaresystem.drivers.webcam_util import capture_snapshot
from bennycaresystem.drivers.honey_driver import push_honey_ml, retract_seconds
from bennycaresystem.drivers.kibble_driver import drop_kibble_bins

# ---- discord setup ----
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
# tree = app_commands.CommandTree(bot) - test remove

# ---- prevent overlapping  runs ----
servo_lock = asyncio.Lock()
camera_lock = asyncio.Lock()
honey_lock = asyncio.Lock()
kibble_lock = asyncio.Lock()

RESCUE_CHANNEL_ID = int(os.getenv("RESCUE_CHANNEL_ID", "0"))  # optional



# ---- handler functions ----

async def handle_snapshot(message: discord.Message):
    async with camera_lock:
        loop = asyncio.get_running_loop()
        try:
            path = await loop.run_in_executor(None, capture_snapshot)
        except Exception as e:
            traceback.print_exc()
            await message.channel.send(
                f"📷 snapshot error: {type(e).__name__}: {e}"
            )
            return

    try:
        await message.channel.send(
            content="📷 snapshot captured",
            file=discord.File(path)
        )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


async def handle_rescue(message: discord.Message):
    async with servo_lock:
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(None, servo_rotate_once)
        except Exception as e:
            await message.channel.send(f"servo error: {type(e).__name__}: {e}")
            return

    if result is None or result is True:
        await message.channel.send("✅ rescue executed")
    else:
        await message.channel.send("⚠️ rescue reported failure")


async def handle_honey(message: discord.Message, parts):
    if len(parts) != 2:
        await message.channel.send("usage: !honey <ml>")
        return

    try:
        ml = float(parts[1])
    except ValueError:
        await message.channel.send("invalid ml value")
        return

    async with honey_lock:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, push_honey_ml, ml)

    if result:
        await message.channel.send(f"🍯 pushed {ml} mL")
    else:
        await message.channel.send("⚠️ honey push rejected or failed")


async def handle_kibble(message: discord.Message, parts):
    if len(parts) != 2:
        await message.channel.send("usage: !kibble <bins>")
        return

    try:
        bins = int(parts[1])
    except ValueError:
        await message.channel.send("invalid bin count")
        return

    async with kibble_lock:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, drop_kibble_bins, bins)

    if result:
        await message.channel.send(f"🥣 dropped {bins} bins")
    else:
        await message.channel.send("⚠️ kibble drop failed")


async def handle_retract(message: discord.Message, parts):
    if len(parts) != 2:
        await message.channel.send("usage: !retract <seconds>")
        return

    try:
        sec = float(parts[1])
    except ValueError:
        await message.channel.send("invalid seconds")
        return

    async with honey_lock:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, retract_seconds, sec)

    if result:
        await message.channel.send(f"↩️ retracted for {sec} seconds")
    else:
        await message.channel.send("⚠️ retract rejected")

# ---- MESSAGE TRIGGER ----
@bot.event
async def on_message(message: discord.Message):
    print("MESSAGE EVENT", message.id, message.content)

    if message.author.bot:
        return

    if RESCUE_CHANNEL_ID and message.channel.id != RESCUE_CHANNEL_ID:
        return

    content = (message.content or "").strip().lower()
    parts = content.split()

    if content == "!snapshot":
        await handle_snapshot(message)

    elif content == "!rescue":
        await handle_rescue(message)

    elif parts[0] == "!honey":
        await handle_honey(message, parts)

    elif parts[0] == "!kibble":
        await handle_kibble(message, parts)

    elif parts[0] == "!retract":
        await handle_retract(message, parts)



# ---- lifecycle ----

@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")

    if RESCUE_CHANNEL_ID:
        channel = bot.get_channel(RESCUE_CHANNEL_ID)
        if channel:
            asyncio.create_task(shadow_protocol_loop(channel))

# ---- shadow mode hook for autoprotocols ----

async def shadow_protocol_loop(channel):
    """
    Watches glucose stream and reports what the protocol
    *would* do without executing actuators.
    """

    while True:

        await asyncio.sleep(60)

        # placeholder
        decision = None

        if decision:
            await channel.send(
                f"[BCS SHADOW]\n"
                f"protocol would intervene: {decision}"
            )

# ---- entry ----
bot.run(BOT_TOKEN)
