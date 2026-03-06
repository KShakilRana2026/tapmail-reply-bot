import os
import requests
import re
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest
from config import BOT_TOKEN, FORCE_CHANNELS, BASE_URL

user_sessions = {}

# ==========================
# MENU
# ==========================
def main_menu():
    keyboard = [
        ["📧 Generate Email", "📥 Inbox"],
        ["🔐 Get OTP", "🔄 Auto Check"],
        ["♻ Reset Email", "ℹ Status"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==========================
# OTP Extract
# ==========================
def extract_otp(text):
    match = re.search(r"\b\d{4,6}\b", text)
    return match.group(0) if match else None

# ==========================
# FORCE JOIN CHECK
# ==========================
def check_join(update, context):
    user_id = update.effective_user.id

    for chat in FORCE_CHANNELS:
        try:
            member = context.bot.get_chat_member(chat, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except BadRequest:
            return False

    return True

# ==========================
# START
# ==========================
def start(update, context):

    if not check_join(update, context):
        update.message.reply_text(
            "🚫 আগে আমাদের Group & Channel Join করুন:\n\n"
            "👉 https://t.me/dark_princes12\n"
            "👉 https://t.me/myfirstchannel12\n\n"
            "Join করে আবার /start চাপুন।"
        )
        return

    update.message.reply_text(
        "🚀 Tap Mail Prime Bot\n\nMenu নিচে আছে 👇",
        reply_markup=main_menu()
    )

# ==========================
# HANDLE BUTTONS
# ==========================
def handle_message(update, context):

    if not check_join(update, context):
        update.message.reply_text(
            "🚫 আগে Group & Channel Join করুন।"
        )
        return

    text = update.message.text
    user_id = update.message.from_user.id

    # Generate Email
    if text == "📧 Generate Email":
        data = requests.get(f"{BASE_URL}/gen").json()
        if data.get("success"):
            user_sessions[user_id] = {
                "email": data["email"],
                "mid": None
            }
            update.message.reply_text(
                f"✅ Email Created\n\n"
                f"{data['email']}\n"
                f"Expiry: {data['expiry']}"
            )

    # Inbox
    elif text == "📥 Inbox":
        session = user_sessions.get(user_id)
        if not session:
            update.message.reply_text("আগে Email Generate করুন")
            return

        data = requests.get(
            f"{BASE_URL}/inbox?email={session['email']}"
        ).json()

        messages = data.get("messages", [])
        if not messages:
            update.message.reply_text("📭 Inbox Empty")
            return

        session["mid"] = messages[0]["mid"]
        update.message.reply_text(
            f"📩 Mail Found\nSubject: {messages[0]['textSubject']}"
        )

    # Get OTP
    elif text == "🔐 Get OTP":
        session = user_sessions.get(user_id)
        if not session or not session.get("mid"):
            update.message.reply_text("আগে Inbox Check করুন")
            return

        msg = requests.get(
            f"{BASE_URL}/message?email={session['email']}&mid={session['mid']}"
        ).json()

        otp = msg.get("otp") or extract_otp(msg.get("full_message", ""))

        if otp:
            update.message.reply_text(f"🔐 OTP: {otp}")
        else:
            update.message.reply_text("OTP পাওয়া যায়নি")

    # Reset
    elif text == "♻ Reset Email":
        user_sessions.pop(user_id, None)
        update.message.reply_text("Session Reset Complete")

    # Status
    elif text == "ℹ Status":
        session = user_sessions.get(user_id)
        if session:
            update.message.reply_text(f"Current Email: {session['email']}")
        else:
            update.message.reply_text("No Active Email")

# ==========================
# MAIN
# ==========================
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Bot Running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
