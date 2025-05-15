# main.py
import os
import logging
import uuid
from typing import List
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
from database import add_user, approve_user, is_approved, get_all_users
from PIL import Image

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Use numeric channel ID (e.g., -1001234567890)
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Your Telegram user ID
from utils import resize_image, is_valid_image

# ইমেজ প্রসেসিং
success = resize_image(
    input_path="input.jpg",
    output_path="output.webp",
    size=(800, 800),
    quality=90,
    format="WEBP",
    preserve_metadata=True
)

# ইমেজ ভ্যালিডেশন
if is_valid_image("user_upload.jpg"):
    print("Valid image file")
else:
    print("Corrupted image file")
# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message and check channel membership."""
    user = update.effective_user
    add_user(user.id, user.username)

    try:
        member = context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(
                f"⚠️ Please join our channel first: {CHANNEL_ID}"
            )
            return
    except Exception as e:
        logger.error(f"Channel check failed: {e}")
        update.message.reply_text("❌ Couldn't verify channel membership. Please try later.")
        return

    if is_approved(user.id):
        update.message.reply_text(
            "🎉 Welcome back! Send me images to process."
        )
    else:
        update.message.reply_text(
            "⌛ Your account is under review. Please wait for admin approval.\n"
            "Use /request_access to notify admin."
        )

def request_access(update: Update, context: CallbackContext) -> None:
    """Notify admin about access request."""
    user = update.effective_user
    context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🆕 Access request from:\n"
             f"User: @{user.username}\n"
             f"ID: {user.id}\n"
             f"Use /approve {user.id} to grant access"
    )
    update.message.reply_text("✅ Admin notified! We'll contact you soon.")

def approve_user_command(update: Update, context: CallbackContext) -> None:
    """Approve a user (admin only)."""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Admin access required!")
        return

    try:
        user_id = int(context.args[0])
        approve_user(user_id)
        
        # Notify the approved user
        context.bot.send_message(
            chat_id=user_id,
            text="🎉 Your access has been approved! Use /start to begin."
        )
        
        update.message.reply_text(f"✅ User {user_id} approved successfully!")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /approve <user_id>")

def handle_images(update: Update, context: CallbackContext) -> None:
    """Process uploaded images."""
    user = update.effective_user
    
    if not is_approved(user.id):
        update.message.reply_text("❌ Your account isn't approved yet!")
        return

    try:
        # Download the highest resolution available
        photo = update.message.photo[-1]
        input_file = f"temp_input_{uuid.uuid4().hex}.jpg"
        output_file = f"temp_output_{uuid.uuid4().hex}.jpg"
        
        photo.get_file().download(input_file)
        
        # Process image
        with Image.open(input_file) as img:
            img.thumbnail((300, 300))  # Resize while maintaining aspect ratio
            img.save(output_file, "JPEG", quality=85)
            
            # Send result back
            with open(output_file, "rb") as photo_file:
                update.message.reply_photo(
                    photo=photo_file,
                    caption="Here's your processed image!"
                )
        
        # Clean up temp files
        os.remove(input_file)
        os.remove(output_file)
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        update.message.reply_text("❌ Failed to process image. Please try another file.")

def broadcast(update: Update, context: CallbackContext) -> None:
    """Send message to all approved users (admin only)."""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Admin access required!")
        return

    if not context.args:
        update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    users = get_all_users()
    success = 0
    failed = 0

    for user_id in users:
        try:
            context.bot.send_message(chat_id=user_id, text=message)
            success += 1
        except Exception as e:
            logger.warning(f"Failed to send to {user_id}: {e}")
            failed += 1

    update.message.reply_text(
        f"📢 Broadcast results:\n"
        f"• Success: {success}\n"
        f"• Failed: {failed}"
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Show help message."""
    commands = [
        "<b>Available Commands:</b>",
        "/start - Begin using the bot",
        "/request_access - Request approval",
        "/help - Show this message",
        "",
        "<b>Admin Commands:</b>",
        "/approve [user_id] - Approve a user",
        "/broadcast [message] - Send message to all users"
    ]
    update.message.reply_text("\n".join(commands), parse_mode="HTML")

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors."""
    logger.error(f"Update {update} caused error: {context.error}")

def main() -> None:
    """Start the bot."""
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("request_access", request_access))
    dp.add_handler(CommandHandler("approve", approve_user_command))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(MessageHandler(Filters.photo & ~Filters.command, handle_images))
    
    # Error handling
    dp.add_error_handler(error_handler)

    # Start polling
    updater.start_polling()
    logger.info("Bot is now running...")
    updater.idle()

if __name__ == "__main__":
    main()
