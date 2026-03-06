import requests
import asyncio
import re
from telegram import (
    Update,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN, BASE_URL

# ==========================
# Storage
# ==========================
user_sessions = {}

# ==========================
# Reply Keyboard
# ==========================
def main_menu():
    keyboard = [
        ["📧 Generate Email", "📥 Inbox"],
        ["🔐 Get OTP", "🔄 Auto Check"],
        ["♻ Reset Email", "ℹ Status"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )

# ==========================
# OTP Extract
# ==========================
def extract_otp(text):
    match = re.search(r"\b\d{4,6}\b", text)
    return match.group(0) if match else None

# ==========================
# API Calls
# ==========================
def generate_email():
    return requests.get(f"{BASE_URL}/gen").json()

def check_inbox(email):
    return requests.get(f"{BASE_URL}/inbox?email={email}").json()

def read_message(email, mid):
    return requests.get(
        f"{BASE_URL}/message?email={email}&mid={mid}"
    ).json()

# ==========================
# Start
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Tap Mail Prime Bot*\n\n"
        "Temporary Email + OTP Service\n\n"
        "👇 নিচের মেনু ব্যবহার করুন",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ==========================
# Button Handler
# ==========================
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # Generate Email
    if text == "📧 Generate Email":
        data = generate_email()
        if data.get("success"):
            user_sessions[user_id] = {
                "email": data["email"],
                "mid": None
            }

            await update.message.reply_text(
                f"✅ *Email Created*\n\n"
                f"📧 `{data['email']}`\n"
                f"⏳ Expiry: {data['expiry']}",
                parse_mode="Markdown"
            )

    # Inbox
    elif text == "📥 Inbox":
        session = user_sessions.get(user_id)

        if not session:
            await update.message.reply_text("⚠ আগে Email Generate করুন")
            return

        data = check_inbox(session["email"])
        messages = data.get("messages", [])

        if not messages:
            await update.message.reply_text("📭 Inbox Empty")
            return

        mid = messages[0]["mid"]
        session["mid"] = mid

        await update.message.reply_text(
            f"📩 *New Mail Found*\n"
            f"Subject: {messages[0]['textSubject']}",
            parse_mode="Markdown"
        )

    # Get OTP
    elif text == "🔐 Get OTP":
        session = user_sessions.get(user_id)

        if not session or not session.get("mid"):
            await update.message.reply_text("⚠ আগে Inbox Check করুন")
            return

        msg = read_message(session["email"], session["mid"])
        otp = msg.get("otp") or extract_otp(msg.get("full_message", ""))

        if otp:
            await update.message.reply_text(
                f"🔐 *OTP Code*\n\n`{otp}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ OTP পাওয়া যায়নি")

    # Auto Check
    elif text == "🔄 Auto Check":
        session = user_sessions.get(user_id)

        if not session:
            await update.message.reply_text("⚠ আগে Email Generate করুন")
            return

        await update.message.reply_text("🔄 30 সেকেন্ড অপেক্ষা করুন...")

        for _ in range(6):
            await asyncio.sleep(5)

            data = check_inbox(session["email"])
            messages = data.get("messages", [])

            if messages:
                mid = messages[0]["mid"]
                session["mid"] = mid

                msg = read_message(session["email"], mid)
                otp = msg.get("otp") or extract_otp(msg.get("full_message", ""))

                if otp:
                    await update.message.reply_text(
                        f"🔔 *Auto OTP Found*\n\n`{otp}`",
                        parse_mode="Markdown"
                    )
                    return

        await update.message.reply_text("⏳ OTP আসেনি")

    # Reset
    elif text == "♻ Reset Email":
        user_sessions.pop(user_id, None)
        await update.message.reply_text("♻ Session Reset Complete")

    # Status
    elif text == "ℹ Status":
        session = user_sessions.get(user_id)
        if session:
            await update.message.reply_text(
                f"📧 Current Email:\n`{session['email']}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ No active session")

# ==========================
# Run
# ==========================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

print("🚀 Bot Running...")
app.run_polling()
