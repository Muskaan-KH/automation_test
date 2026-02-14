
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN, ADMIN_CHAT_ID, WELCOME_MESSAGE, REFERRAL_REWARD, FRIEND_REWARD
from database import db
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# COMMAND: /start - New users + Referral tracking
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command. This is your opt-in AND referral tracker."""
    
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    # Check if this is a referral (user clicked referral link)
    referred_by = None
    if context.args:
        # The argument is the referrer's chat_id
        referred_by = context.args[0]
        logger.info(f"➕ Referral detected! {chat_id} referred by {referred_by}")
    
    # Add user to database
    db_user = db.add_user(
        chat_id=chat_id,
        first_name=user.first_name,
        username=user.username,
        referred_by=referred_by
    )
    
    # Get bot username for referral link
    bot_username = (await context.bot.get_me()).username
    
    # Personalize welcome message
    welcome = WELCOME_MESSAGE.format(
        name=user.first_name,
        bot_username=bot_username,
        chat_id=chat_id,
        reward=REFERRAL_REWARD
    )
    
    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton("🔗 GET YOUR REFERRAL LINK", callback_data='get_link')],
        [InlineKeyboardButton("📊 MY STATS", callback_data='stats')],
        [InlineKeyboardButton("🎁 HOW IT WORKS", callback_data='how_it_works')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message
    await update.message.reply_text(
        welcome,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    # If user was referred, notify the referrer
    if referred_by and referred_by in db.data['users']:
        try:
            await context.bot.send_message(
                chat_id=int(referred_by),
                text=f"🎉 **Congratulations!**\n\n"
                     f"{user.first_name} joined using your referral link!\n"
                     f"You now have {db.data['users'][referred_by]['referrals']} referrals.\n\n"
                     f"Your {REFERRAL_REWARD} is ready! 🎁",
                parse_mode='Markdown'
            )
            logger.info(f"✅ Referral notification sent to {referred_by}")
        except Exception as e:
            logger.error(f"❌ Failed to notify referrer {referred_by}: {e}")
    
    # Log message sent
    db.log_message_sent(chat_id, 'welcome')


# ============================================
# COMMAND: /referral - Get referral link
# ============================================
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send user their personalized referral link."""
    
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    # Update last active
    db.update_last_active(chat_id)
    
    # Get bot username
    bot_username = (await context.bot.get_me()).username
    
    # Create referral link
    referral_link = f"https://t.me/{bot_username}?start={chat_id}"
    
    # Get user's current referrals
    db_user = db.get_user(chat_id)
    referrals = db_user.get('referrals', 0) if db_user else 0
    
    # Create share buttons
    keyboard = [
        [InlineKeyboardButton("📤 SHARE LINK", url=f"https://t.me/share/url?url={referral_link}&text=Join%20me%20on%20this%20referral%20program%20for%20{REFERRAL_REWARD.replace('%', '%25')}")],
        [InlineKeyboardButton("📋 COPY LINK", callback_data='copy_link')],
        [InlineKeyboardButton("◀️ BACK", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""
🔗 **YOUR PERSONAL REFERRAL LINK**

`{referral_link}`

📊 **Your Stats:**
• Referrals: **{referrals}**
• Reward: {REFERRAL_REWARD if referrals > 0 else 'Not yet'}

Share this link with friends!
When they join, you BOTH get rewards.
"""
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    
    db.log_message_sent(chat_id, 'referral_link')


# ============================================
# COMMAND: /stats - View personal stats
# ============================================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user their referral statistics."""
    
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    db_user = db.get_user(chat_id)
    
    if not db_user:
        await update.message.reply_text("Please /start first to join the program!")
        return
    
    referrals = db_user.get('referrals', 0)
    
    message = f"""
📊 **YOUR REFERRAL STATISTICS**

👤 Name: {user.first_name}
🔢 User ID: `{chat_id}`
📅 Joined: {db_user.get('joined_at', 'N/A')[:10]}

🎁 **Performance:**
• Total Referrals: **{referrals}**
• Reward Earned: {REFERRAL_REWARD if referrals > 0 else 'Not yet'}
• Status: {db_user.get('status', 'active').upper()}

🔗 Get your link: /referral
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')
    db.update_last_active(chat_id)


# ============================================
# COMMAND: /broadcast - ADMIN ONLY - Send to X contacts
# ============================================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ADMIN COMMAND: Send referral campaign to X users"""
    
    # Verify admin
    if update.effective_chat.id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ This command is for admins only.")
        return
    
    # Check if limit provided
    if not context.args:
        await update.message.reply_text(
            "Usage: /broadcast [number]\n"
            "Example: /broadcast 50 - sends to first 50 active users"
        )
        return
    
    try:
        limit = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid number")
        return
    
    # Get active users up to limit
    users = db.get_active_users(limit=limit)
    
    if not users:
        await update.message.reply_text("❌ No active users found")
        return
    
    # Campaign message
    campaign_message = """
🎁 **DOUBLE REFERRAL WEEKEND** 🎁

**For 48 hours only:**
Refer 2 friends → Get **50% OFF** your next purchase!

Your friends get 30% OFF!

🔗 Get your referral link: /referral

Share now and save big! 🚀
"""
    
    # Send to users
    sent_count = 0
    failed_count = 0
    
    status_message = await update.message.reply_text(
        f"📤 Sending campaign to {len(users)} users..."
    )
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=int(user['chat_id']),
                text=campaign_message,
                parse_mode='Markdown'
            )
            db.log_message_sent(user['chat_id'], 'campaign')
            sent_count += 1
            
            # Rate limiting - 1 second between messages
            import asyncio
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to send to {user['chat_id']}: {e}")
            failed_count += 1
    
    # Update status
    await status_message.edit_text(
        f"✅ **Campaign Complete**\n\n"
        f"📤 Target: {limit}\n"
        f"✅ Sent: {sent_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"📊 Total in DB: {db.data['total_users']}"
    )


# ============================================
# COMMAND: /export - ADMIN ONLY - Get ALL contacts
# ============================================
async def export_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ADMIN COMMAND: Export all contacts as CSV"""
    
    # Verify admin
    if update.effective_chat.id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ This command is for admins only.")
        return
    
    import csv
    import io
    
    all_users = db.get_all_users()
    
    if not all_users:
        await update.message.reply_text("❌ No users in database")
        return
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        'chat_id', 'first_name', 'username', 'joined_date', 
        'referred_by', 'referrals', 'last_active', 'status'
    ])
    
    # Write user data
    for chat_id, user in all_users.items():
        writer.writerow([
            chat_id,
            user.get('first_name', ''),
            user.get('username', ''),
            user.get('joined_at', ''),
            user.get('referred_by', ''),
            user.get('referrals', 0),
            user.get('last_active', ''),
            user.get('status', '')
        ])
    
    # Send file
    output.seek(0)
    await update.message.reply_document(
        document=output.getvalue().encode('utf-8'),
        filename=f'telegram_contacts_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        caption=f"✅ Exported {len(all_users)} contacts"
    )


# ============================================
# Button callback handlers
# ============================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_chat.id)
    bot_username = (await context.bot.get_me()).username
    db_user = db.get_user(chat_id)
    referrals = db_user.get('referrals', 0) if db_user else 0
    
    if query.data == 'get_link':
        referral_link = f"https://t.me/{bot_username}?start={chat_id}"
        await query.edit_message_text(
            f"🔗 **Your Referral Link**\n\n"
            f"`{referral_link}`\n\n"
            f"📊 **Current referrals:** {referrals}\n\n"
            f"Copy and share this link!",
            parse_mode='Markdown'
        )
    
    elif query.data == 'stats':
        message = f"""
📊 **Your Stats**

✅ Referrals: **{referrals}**
🎁 Reward: {REFERRAL_REWARD if referrals > 0 else 'Not yet'}

Share your link to earn! /referral
"""
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif query.data == 'how_it_works':
        message = f"""
🎁 **How It Works**

1️⃣ Get your unique referral link
2️⃣ Share with friends
3️⃣ They join using your link
4️⃣ You BOTH get {REFERRAL_REWARD}

Unlimited referrals!

🔗 Get your link: /referral
"""
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif query.data == 'copy_link':
        await query.answer("Copy this link manually", show_alert=True)
    
    elif query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("🔗 GET YOUR REFERRAL LINK", callback_data='get_link')],
            [InlineKeyboardButton("📊 MY STATS", callback_data='stats')],
            [InlineKeyboardButton("🎁 HOW IT WORKS", callback_data='how_it_works')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🏠 **Main Menu**\n\nChoose an option:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


# ============================================
# Error handler
# ============================================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")


# ============================================
# Main function
# ============================================
def main():
    """Start the bot"""
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("export", export_contacts))
    
    # Add button callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("🤖 Telegram Referral Bot is starting...")
    print(f"✅ Admin chat ID: {ADMIN_CHAT_ID}")
    print("✅ Database: users_database.json")
    print("✅ Commands loaded: /start, /referral, /stats, /broadcast, /export")
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()