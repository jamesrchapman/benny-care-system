import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv
import traceback

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
tree = app_commands.CommandTree(bot)

# ---- prevent overlapping  runs ----
servo_lock = asyncio.Lock()
camera_lock = asyncio.Lock()
honey_lock = asyncio.Lock()
kibble_lock = asyncio.Lock()

RESCUE_CHANNEL_ID = int(os.getenv("RESCUE_CHANNEL_ID", "0"))  # optional


# ---- MESSAGE TRIGGER (NEW) ----
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if RESCUE_CHANNEL_ID and message.channel.id != RESCUE_CHANNEL_ID:
        return

    content = (message.content or "").strip().lower()

    if content in ("!snapshot", "snapshot"):
        async with camera_lock:
            loop = asyncio.get_running_loop()
            try:
                path = await loop.run_in_executor(None, capture_snapshot)
            except Exception as e:
                traceback.print_exc()   # 👈 THIS is the missing piece
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

    if content in ("!rescue", "rescue"):
        async with servo_lock:
            loop = asyncio.get_running_loop()
            try:
                result = await loop.run_in_executor(None, servo_rotate_once)
            except Exception as e:
                await message.channel.send(f"servo error: {type(e).__name__}: {e}")
                return

        if result is None or result is True:
            await message.channel.send("✅ rescue executed (message trigger)")
        else:
            await message.channel.send("⚠️ rescue reported failure (message trigger)")
    
        if content.startswith("!honey"):
            parts = content.split()
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


        elif content.startswith("!kibble"):
            parts = content.split()
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
        elif content.startswith("!retract"):
            parts = content.split()
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


# ---- slash command ----
@tree.command(name="rescue", description="Run the rescue servo once.")
async def rescue_cmd(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    async with servo_lock:
        loop = asyncio.get_running_loop()
        try:
            # run blocking GPIO code off the event loop
            result = await loop.run_in_executor(None, servo_rotate_once)
        except Exception as e:
            await interaction.followup.send(f"servo error: {type(e).__name__}: {e}")
            return

    # treat None as success
    if result is None or result is True:
        await interaction.followup.send("✅ rescue executed")
    else:
        await interaction.followup.send("⚠️ rescue reported failure")

@tree.command(name="snapshot", description="Capture an image from the Pi camera.")
async def snapshot_cmd(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    async with camera_lock:
        loop = asyncio.get_running_loop()
        try:
            path = await loop.run_in_executor(None, capture_snapshot)
        except Exception as e:
            await interaction.followup.send(f"📷 snapshot error: {type(e).__name__}: {e}")
            return
        

    try:
        await interaction.followup.send(
            content="📷 snapshot captured",
            file=discord.File(path)
        )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ---- lifecycle ----
@bot.event
async def setup_hook():
    await tree.sync()
    print("slash commands synced")


@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


# ---- entry ----
bot.run(BOT_TOKEN)
