import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create self-bot with command prefix and no intents.
# Disable guild subscriptions and member chunking for user token usage.
bot = commands.Bot(
    command_prefix='.',
    help_command=None,
    self_bot=True,
    guild_subscriptions=False,
    chunk_guilds_at_startup=False,
    member_cache_flags=discord.MemberCacheFlags.none(),
)

# Track users who have DMed the bot
dmed_users = set()
# Track active mdm tasks
active_mdm_tasks = {}
# Track AFK status
is_afk = False

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    # Set online streaming presence from .env
    stream_name = os.getenv('STREAM_NAME')
    if not stream_name:
        stream_name = 'a stream'
        print('WARN: STREAM_NAME not set, defaulting to "a stream"')
    else:
        print(f'STREAM_NAME loaded: {stream_name}')

    activity = discord.Activity(
        type=discord.ActivityType.streaming,
        name=stream_name,
        url="https://www.twitch.tv/hh",
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_message(message):
    # For self-bots, we want to process commands from our own user
    # So we do NOT ignore messages from bot.user
    
    # Track users who DM the bot
    if isinstance(message.channel, discord.DMChannel):
        dmed_users.add(message.author.id)
    
    # Check if the bot is mentioned in the message and AFK is currently enabled
    if bot.user in message.mentions and is_afk:
        # Capture the AFK state at the time of mention
        was_afk_when_mentioned = is_afk
        # Wait 15 seconds
        await asyncio.sleep(15)
        # Only reply if AFK was enabled when mentioned AND still enabled now
        if was_afk_when_mentioned and is_afk:
            await message.reply('hello, i am busy rn')
    
    # Process commands
    await bot.process_commands(message)

# Check to ensure only the bot can run a command
def bot_only():
    """Decorator to restrict command to bot user only"""
    async def predicate(ctx):
        if ctx.author != ctx.bot.user:
            raise commands.CheckFailure()
        return True
    return commands.check(predicate)

@bot.command(name='join')
@bot_only()
async def join(ctx, channel: discord.VoiceChannel = None):
    """Bot joins a voice channel. If no channel is provided, joins the invoker's voice channel."""
    status_msg = None
    try:
        status_msg = await ctx.send("Joining voice channel...")

        # Fallback to author's voice channel when not provided
        if channel is None:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await status_msg.edit(content="✗ No channel provided and you are not in a voice channel.")
                return

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        voice_client = await channel.connect()

        # Deafen and mute the self-bot after connecting
        try:
            await ctx.guild.change_voice_state(ctx.guild.me, channel, self_mute=True, self_deaf=True)
        except Exception:
            # Best-effort: ignore if permission or API difference prevents changing state
            pass

        await status_msg.edit(content=f"✓ Joined {channel.name} (self-muted & self-deafened)")
    except Exception as e:
        if status_msg:
            await status_msg.edit(content=f"✗ Error joining channel: {e}")
        else:
            await ctx.send(f"✗ Error joining channel: {e}")

@bot.command(name='l2l')
@bot_only()
async def l2l(ctx, channel: discord.VoiceChannel = None):
    """Bot joins a voice channel and leaves if no users are present every 20 seconds.
    If no channel is provided, joins the invoker's voice channel."""
    status_msg = None
    try:
        status_msg = await ctx.send("Joining voice channel...")

        # Fallback to author's voice channel when not provided
        if channel is None:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await status_msg.edit(content="✗ No channel provided and you are not in a voice channel.")
                return

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        voice_client = await channel.connect()

        # Deafen and mute the self-bot after connecting
        try:
            await ctx.guild.change_voice_state(ctx.guild.me, channel, self_mute=True, self_deaf=True)
        except Exception:
            pass

        await status_msg.edit(content=f"✓ Joined {channel.name} (monitoring for users; self-muted & self-deafened)")

        # Start background task to check for users every 20 seconds
        while True:
            await asyncio.sleep(20)

            # Determine the current voice client robustly. Prefer the context's
            # voice client when available, then the guild's, then the local
            # `voice_client` returned by `connect()`.
            current_vc = None
            if getattr(ctx, "voice_client", None):
                current_vc = ctx.voice_client
            elif ctx.guild and getattr(ctx.guild, "voice_client", None):
                current_vc = ctx.guild.voice_client
            else:
                current_vc = voice_client

            # If we're no longer connected, stop monitoring
            if current_vc is None or not getattr(current_vc, "channel", None):
                break

            # Check if there are any non-bot users in the channel (exclude self by id)
            users_in_channel = [member for member in current_vc.channel.members if member.id != bot.user.id and not member.bot]

            if not users_in_channel:
                try:
                    await current_vc.disconnect()
                except Exception:
                    pass
                await status_msg.edit(content=f"✓ Left {channel.name} (no users detected)")
                break
    except Exception as e:
        if status_msg:
            await status_msg.edit(content=f"✗ Error in l2l command: {e}")
        else:
            await ctx.send(f"✗ Error in l2l command: {e}")

@bot.command(name='mdm')
@bot_only()
async def mdm(ctx, *, message=None):
    """Bot sends a message to everyone it has DMed with. Use '.mdm stop' to cancel"""
    try:
        # Handle stop command
        if message and message.lower() == 'stop':
            if ctx.guild.id in active_mdm_tasks:
                active_mdm_tasks[ctx.guild.id]['task'].cancel()
                await ctx.send("MDM process stopped.")
            else:
                await ctx.send("No active MDM process to stop.")
            return
        
        if not message:
            await ctx.send("Please provide a message. Usage: `.mdm [message]` or `.mdm stop`")
            return
        
        if not dmed_users:
            await ctx.send("No users to DM yet.")
            return
        
        # Send initial status message
        status_msg = await ctx.send(f"Sending message to {len(dmed_users)} users...")
        
        # Create the actual sending task
        async def send_messages():
            success_count = 0
            failed_count = 0
            
            for user_id in dmed_users:
                try:
                    user = await bot.fetch_user(user_id)
                    await user.send(message)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to DM user {user_id}: {e}")
            
            # Edit the status message with results
            await status_msg.edit(content=f"**Success:** {success_count}\n**Failed:** {failed_count}")
            
            # Remove task from tracking
            if ctx.guild.id in active_mdm_tasks:
                del active_mdm_tasks[ctx.guild.id]
        
        # Create and store the task
        task = asyncio.create_task(send_messages())
        active_mdm_tasks[ctx.guild.id] = {'task': task, 'message': message}
        
    except asyncio.CancelledError:
        # Task was cancelled
        pass
    except Exception as e:
        await ctx.send(f"Error in mdm command: {e}")

@bot.command(name='afk')
@bot_only()
async def afk(ctx):
    """Toggle AFK status (enables/disables busy response when mentioned)"""
    global is_afk
    try:
        is_afk = not is_afk
        status = "✓ AFK mode enabled" if is_afk else "✓ AFK mode disabled"
        status_msg = await ctx.send(status)
    except Exception as e:
        await ctx.send(f"Error in afk command: {e}")

@bot.command(name='help')
@bot_only()
async def help_command(ctx):
    """Display all available commands"""
    try:
        help_text = (
            "Bot Commands:\n"
            "Here are all available commands:\n\n"
            "`.join <channel>` - Bot joins a specified voice channel\n"
            "`.l2l <channel>` - Bot joins a voice channel and automatically leaves if no users are present (checks every 20 seconds)\n"
            "`.mdm [message]` - Send a message to all users who have DMed the bot\n"
            "`.mdm stop` - Force stop an ongoing MDM (mass DM) operation\n"
            "`.afk` - Toggle AFK mode on/off. When enabled, bot replies with 'hello, i am busy rn' when mentioned\n"
            "`.help` - Display this help message\n\n"
            "All commands can only be executed by the bot itself"
        )
        await ctx.send(help_text)
    except Exception as e:
        await ctx.send(f"Error in help command: {e}")

# Run the self-bot with a user token from .env
# Ensure TOKEN is a valid Discord user token, not a bot token.
bot.run(os.getenv('TOKEN'))
