import os
from dotenv import load_dotenv
import json
from pathlib import Path

# Load environment variables
load_dotenv() 

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '0'))

# Database file path
DB_PATH = Path('users_database.json')

# Referral reward settings
REFERRAL_REWARD = "20% OFF your next purchase"
FRIEND_REWARD = "20% OFF their first purchase"

# Welcome message template
WELCOME_MESSAGE = """
👋 Welcome {name}!

🎁 **REFERRAL PROGRAM ACTIVATED**

Your personal referral link:
🔗 https://t.me/{bot_username}?start={chat_id}

**How it works:**
1. Share this link with friends
2. They click and start the bot
3. You BOTH get {reward}!

Commands:
/referral - Get your link
/stats - Your referral count
/help - Help

Happy referring! 🚀
"""

# Verify bot token is set
if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN not set in .env file!")