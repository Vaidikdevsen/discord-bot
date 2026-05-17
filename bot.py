import discord
from discord.ext import commands
import asyncio

# Create bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if the bot is mentioned in the message
    if bot.user.mentioned_in(message):
        # Wait 15 seconds
        await asyncio.sleep(15)
        # Reply with the message
        await message.reply('Hello, I am busy')
    
    # Process other commands if any
    await bot.process_commands(message)

# Run the bot
bot.run('YOUR_DISCORD_BOT_TOKEN_HERE')