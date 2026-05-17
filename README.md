# Discord Bot

A feature-rich Discord bot with voice channel management, mass messaging, and AFK mode capabilities.

## Features

- **Voice Channel Management**: Join voice channels and monitor for users
- **Mass Direct Messaging**: Send messages to all users who have DMed the bot
- **AFK Mode**: Toggle auto-response when mentioned
- **Streaming Status**: Display custom streaming status from environment variables
- **Bot-Only Commands**: All commands can only be executed by the bot itself

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd discord-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to "Bot" section and click "Add Bot"
4. Under "TOKEN", click "Copy" to copy your bot token
5. Go to "OAuth2" > "URL Generator"
6. Select scopes: `bot`
7. Select permissions:
   - Send Messages
   - Read Message History
   - Mention @everyone, @here, and All Roles
   - Connect (to voice channels)
   - Speak (in voice channels)
8. Copy the generated URL and open it in your browser to invite the bot to your server

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
STREAM_NAME=Your Stream Name Here
```

Replace `your_bot_token_here` with your actual bot token from the Developer Portal.
Replace `Your Stream Name Here` with the name you want to display in the bot's streaming status.

### 5. Run the Bot

```bash
python bot.py
```

You should see in the terminal:
```
YourBotName#1234 has connected to Discord!
```

## Commands

All commands use the `.` prefix and **can only be executed by the bot itself**.

### 1. `.join <channel>`
Makes the bot join a specified voice channel.

**Usage:**
```
.join General
```

**Response:**
- Initial: `Joining voice channel...`
- Success: `✓ Joined General`
- Error: `✗ Error joining channel: [error details]`

---

### 2. `.l2l <channel>`
"Lurk to Leave" - Bot joins a voice channel and automatically leaves when no users are present.

The bot checks for users every 20 seconds. If only the bot is in the channel, it disconnects automatically.

**Usage:**
```
.l2l General
```

**Response:**
- Initial: `Joining voice channel...`
- Joined: `✓ Joined General (monitoring for users)`
- Departure: `✓ Left General (no users detected)`

**How it works:**
1. Bot joins the specified channel
2. Every 20 seconds, checks for non-bot users
3. If no users found, disconnects and updates the message
4. Loop stops when channel is empty or bot disconnects

---

### 3. `.mdm [message]`
"Mass Direct Message" - Sends a message to all users who have previously DMed the bot.

**Usage:**
```
.mdm Hello everyone! This is a broadcast message.
```

**Response:**
- Initial: `Sending message to 5 users...`
- Completion: 
  ```
  **Success:** 5
  **Failed:** 0
  ```

**Stopping the operation:**
```
.mdm stop
```

**Response:**
```
MDM process stopped.
```

**How it works:**
1. Bot tracks all users who send it a DM
2. When `.mdm` is used, it sends the message to all tracked users asynchronously
3. Messages are sent in the background without blocking
4. Status message shows how many users receive the message and any failures
5. Can be cancelled mid-operation with `.mdm stop`

---

### 4. `.afk`
Toggle AFK (Away From Keyboard) mode on/off.

When AFK is enabled, the bot will reply with "Hello, I am busy" when mentioned (after 15 seconds).
When AFK is disabled, the bot ignores all mentions.

**Usage:**
```
.afk
```

**Response:**
- Enabling: `✓ AFK mode enabled`
- Disabling: `✓ AFK mode disabled`

**How it works:**
1. Run `.afk` to toggle the status
2. When enabled and bot is mentioned: waits 15 seconds, then replies "Hello, I am busy"
3. When disabled: bot ignores all mentions
4. Status persists until toggled again

---

### 5. `.help`
Displays all available commands with descriptions in a formatted embed.

**Usage:**
```
.help
```

**Response:** A formatted embed showing all commands, their usage, and descriptions.

---

## How It Works

### Event Handlers

**`on_ready` Event:**
- Fires when bot successfully connects to Discord
- Prints connection confirmation
- Sets streaming status from `STREAM_NAME` environment variable

**`on_message` Event:**
- Runs for every message in the server
- Tracks users who DM the bot (stores their user IDs)
- Responds to mentions if AFK mode is enabled
- Processes commands (messages starting with `.`)

### Bot-Only Decorator

All commands use a custom `@bot_only()` decorator that:
- Checks if the command executor is the bot user
- Silently fails if anyone else (user or bot) tries to run the command
- No error messages are sent to unauthorized users

### Message Editing Pattern

All commands follow this pattern:
1. Send initial status message (e.g., "Processing...")
2. Perform action
3. Edit that message with final result

This keeps the chat clean - only one message per command instead of multiple responses.

---

## Configuration

### .env File Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | Your bot's Discord API token | `MTk4NjIyNDgzMjExNjc4NzM2.C-lWgQ...` |
| `STREAM_NAME` | What appears in bot's "Streaming X" status | `My Cool Stream` |

---

## Troubleshooting

### Bot doesn't respond to commands
- Ensure the bot has "Read Message History" and "Send Messages" permissions in the channel
- Make sure you're using the correct prefix (`.`)
- Check that you're running the command, not another user

### "Token is invalid" error
- Verify your token is correct in the `.env` file
- Don't share your token with anyone
- If leaked, regenerate it in the Developer Portal

### Bot can't join voice channels
- Ensure the bot has "Connect" and "Speak" permissions in the server
- Check that the channel is a voice channel (not text)
- Bot must be able to access the channel

### Bot not tracking DM users
- Users must send a message to the bot first (not just mention it)
- DMs are tracked automatically when received
- User IDs are stored for the duration the bot is running

---

## File Structure

```
discord-bot/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .env               # Environment variables (create this)
```

---

## Requirements

See `requirements.txt` for all dependencies. Main requirements:
- `discord.py` - Discord bot framework
- `python-dotenv` - Load environment variables

---

## License

[Add your license here]

---

## Support

For issues or questions, please create an issue in the repository.