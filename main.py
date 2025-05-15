import os
from dotenv import load_dotenv
import logging 
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from database import add_user, approve_user, is_approved, get_all_users
from PIL import Image
load_dotenv()
# Load bot token and channel ID from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Telegram channel username (e.g., "@YourChannel")

# Set up logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Admin user ID (replace with your Telegram ID)
ADMIN_ID =7796887669  # Replace with your Telegram user ID

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Check if user is in the channel
    member_status = context.bot.get_chat_member(CHANNEL_ID, user_id).status
    if member_status not in ["member", "administrator", "creator"]:
        update.message.reply_text(f"You must join {CHANNEL_ID} before using this bot!")
        return

    # Add user to database
    add_user(user_id, username)

    if is_approved(user_id):
        update.message.reply_text("Welcome! Send images to change thumbnails in bulk.")
    else:
        update.message.reply_text("You are not approved to use this bot. Please request access.")

def request_access(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Notify admin for approval
    context.bot.send_message(chat_id=ADMIN_ID, text=f"User @{username} (ID: {user_id}) requested access.")

    update.message.reply_text("Your request has been sent to the admin. Please wait for approval.")

def approve_user_command(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text("Only the admin can approve users.")
        return

    try:
        user_id = int(context.args[0])
        approve_user(user_id)
        update.message.reply_text(f"User {user_id} has been approved!")
    except:
        update.message.reply_text("Invalid user ID. Use: /approve <user_id>")

def handle_images(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if not is_approved(user_id):
        update.message.reply_text("You are not approved to use this bot.")
        return

    for photo in update.message.photo:
        file = context.bot.get_file(photo.file_id)
        file.download("input.jpg")

        # Process image (resize example)
        img = Image.open("input.jpg")
        img.thumbnail((300, 300))
        img.save("output.jpg")

        update.message.reply_photo(photo=open("output.jpg", "rb"), caption="Thumbnail updated!")

def broadcast(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text("Only the admin can send broadcasts.")
        return

    message = " ".join(context.args)
    if not message:
        update.message.reply_text("Usage: /broadcast <message>")
        return

    users = get_all_users()
    for user_id in users:
        context.bot.send_message(chat_id=user_id, text=message)

    update.message.reply_text("Broadcast sent to all approved users!")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("request_access", request_access))
    dp.add_handler(CommandHandler("approve", approve_user_command, pass_args=True))
    dp.add_handler(CommandHandler("broadcast", broadcast, pass_args=True))
    dp.add_handler(MessageHandler(Filters.photo, handle_images))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
