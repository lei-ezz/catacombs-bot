import os
import json
import asyncio
import logging
from datetime import datetime
import discord
from discord.ext import commands, tasks
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='>', intents=intents)

# Configuration
BIRTHDAY_FILE = "birthdays.json"
bday_channel_id = 1336781524045135997
bday_role_id = 1338140324572430376

def load_birthdays():
    try:
        with open(BIRTHDAY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Failed to load birthdays from {BIRTHDAY_FILE}.")
        return {}

def save_birthdays():
    with open(BIRTHDAY_FILE, "w") as f:
        json.dump(birthdays, f, indent=4)

birthdays = load_birthdays()

class User:
    def __init__(self, birthday, timezone="UTC", message="Happy Birthday!"):
        self.birthday = birthday
        self.timezone = timezone
        self.message = message
    
    def to_dict(self):
        return {"birthday": self.birthday, "timezone": self.timezone, "message": self.message}

@tasks.loop(hours=24)
async def check_birthdays():
    for user_id, data in birthdays.items():
        user_data = User(**data)
        tz = pytz.timezone(user_data.timezone)
        today = datetime.now(tz).strftime("%m-%d")
        if user_data.birthday[5:] == today:
            channel = bot.get_channel(bday_channel_id)
            if channel:
                await channel.send(f"{user_data.message} <@{user_id}>! 🎉")

@bot.command(name='set_birthday')
async def set_birthday(ctx, date: str, timezone: str = "UTC", *, message: str = "Happy Birthday!"):
    try:
        datetime.strptime(date, "%m-%d-%Y")
        if timezone not in pytz.all_timezones:
            await ctx.send("Invalid timezone. Please provide a valid timezone from the IANA database.")
            return
        
        birthdays[str(ctx.author.id)] = User(date, timezone, message).to_dict()
        save_birthdays()
        await ctx.send(f"Birthday set to {date} in timezone {timezone} with message: {message}")
    except ValueError:
        await ctx.send("Invalid date format. Use MM-DD-YYYY.")

@bot.command(name='list_birthdays')
async def list_birthdays(ctx):
    output = "\n".join([f"<@{uid}>: {data['birthday']} ({data['timezone']}) - {data['message']}" for uid, data in birthdays.items()])
    await ctx.send(output if output else "No birthdays stored.")

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    check_birthdays.start()
    channel = bot.get_channel(bday_channel_id)
    if channel:
        await channel.send("[DEBUG] Birthday bot is online! 🎂")

bot.run(TOKEN)
