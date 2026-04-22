from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup
import requests
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio
import pandas as pd
from datetime import datetime

# ====== CONFIG ======
TOKEN = "SENING_TOKEN"
API_URL = "SENING_GOOGLE_SCRIPT_URL"

ADMIN_ID = 123456789  # ozingni ID yoz

USERS = set()

# ====== RAILWAY SERVER ======
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ============================================


# ====== API DATA ======
def get_data(data_type):
    try:
        res = requests.get(API_URL + f"?type={data_type}")
        return res.json()
    except:
        return {"error": "API ishlamadi"}


# ====== START ======
async def start(update, context):
    chat_id = update.effective_chat.id
    USERS.add(chat_id)

    keyboard = [
        ["📊 Umumiy", "⚡ Real-time"],
        ["👨‍💼 Hodimlar", "📁 Excel"],
        ["📅 Kunlik"]
    ]

    await update.message.reply_text(
        "Bot ishlayapti 👌",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# ====== HANDLE ======
async def handle(update, context):
    text = update.message.text
    chat_id = update.effective_chat.id

    # ===== UMUMIY =====
    if text == "📊 Umumiy":
        data = get_data("umumiy")
        await update.message.reply_text(f"📊 Umumiy:\n{data}")

    # ===== REALTIME =====
    elif text == "⚡ Real-time":
        data = get_data("realtime")
        await update.message.reply_text(f"⚡ Real-time:\n{data}")

    # ===== HODIMLAR =====
    elif text == "👨‍💼 Hodimlar":
        data = get_data("hodimlar")
        await update.message.reply_text(f"👨‍💼 Hodimlar:\n{data}")

    # ===== EXCEL =====
    elif text == "📁 Excel":
        data = get_data("excel")

        try:
            df = pd.DataFrame(data)
            file_name = "hisobot.xlsx"
            df.to_excel(file_name, index=False)

            await update.message.reply_document(open(file_name, "rb"))

            os.remove(file_name)
        except:
            await update.message.reply_text("❌ Excel xato")

    # ===== KUNLIK =====
    elif text == "📅 Kunlik":
        data = get_data("kunlik")
        await update.message.reply_text(f"📅 Bugungi hisobot:\n{data}")

    # ===== ADMIN PANEL =====
    elif text == "/admin":
        if chat_id == ADMIN_ID:
            await update.message.reply_text(
                f"👑 Admin panel\n\nUserlar soni: {len(USERS)}"
            )
        else:
            await update.message.reply_text("❌ Ruxsat yo‘q")


# ====== AUTO HISOBOT ======
async def auto_send(app):
    while True:
        try:
            data = get_data("umumiy")

            for user in USERS:
                await app.bot.send_message(
                    chat_id=user,
                    text=f"📊 Avto hisobot:\n{data}"
                )

        except:
            pass

        await asyncio.sleep(86400)  # 24 soat


# ====== MAIN ======
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("Bot ishlayapti...")

    asyncio.create_task(auto_send(app))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
