import os
import asyncio
import discord
# from discord import app_commands - allegedly unneeded.
from dotenv import load_dotenv
import traceback


from datetime import datetime


# ---- load env ----
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")



if not BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN not set")

# ---- import hardware action ----
from bennycaresystem.drivers.webcam_util import capture_snapshot
from bennycaresystem.drivers.kibble_driver import drop_kibble_bins
from bennycaresystem.drivers.honey_driver import (
    push_honey_ml,
    push_honey_g,
    retract_ml,
    retract_g,
)
from bennycaresystem.status.status_builder import build_status


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
        path = await loop.run_in_executor(None, capture_snapshot)

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

async def handle_status(message: discord.Message):

    status_text = build_status(
        honey_lock,
        kibble_lock,
        camera_lock
    )

    await message.channel.send(f"```\n{status_text}\n```")

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
        await message.channel.send("usage: !retract <ml>")
        return

    try:
        ml = float(parts[1])
    except ValueError:
        await message.channel.send("invalid ml value")
        return

    async with honey_lock:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, retract_ml, ml)

    if result:
        await message.channel.send(f"↩️ retracted {ml} mL")
    else:
        await message.channel.send("⚠️ retract rejected")

async def handle_retractg(message: discord.Message, parts):
    if len(parts) != 2:
        await message.channel.send("usage: !retractg <grams>")
        return

    try:
        grams = float(parts[1])
    except ValueError:
        await message.channel.send("invalid gram value")
        return

    async with honey_lock:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, retract_g, grams)

    if result:
        await message.channel.send(f"↩️ retracted {grams} g honey")
    else:
        await message.channel.send("⚠️ retract rejected")

async def handle_honeyg(message: discord.Message, parts):
    if len(parts) != 2:
        await message.channel.send("usage: !honeyg <grams>")
        return

    try:
        grams = float(parts[1])
    except ValueError:
        await message.channel.send("invalid gram value")
        return

    async with honey_lock:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, push_honey_g, grams)

    if result:
        await message.channel.send(f"🍯 pushed {grams} g honey")
    else:
        await message.channel.send("⚠️ honey push rejected or failed")

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
    
    elif parts[0] == "!honey":
        await handle_honey(message, parts)

    elif parts[0] == "!kibble":
        await handle_kibble(message, parts)

    elif parts[0] == "!retract":
        await handle_retract(message, parts)

    elif parts[0] == "!retractg":
        await handle_retractg(message, parts)
        
    elif parts[0] == "!honeyg":
        await handle_honeyg(message, parts)
    elif parts[0] == "!status":
        status_text = build_status(
            honey_lock,
            kibble_lock,
            camera_lock
        )

        await message.channel.send(
            f"```\n{status_text}\n```"
        )



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
