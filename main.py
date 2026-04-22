from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup
import requests
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio

TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

# 🔥 ADMINLAR (avtomatik yig'iladi)
ADMINS = set()


# ===== Railway server =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ==========================


# ===== API =====
def get_data(t):
    try:
        res = requests.get(API_URL + f"?type={t}")
        return res.text
    except:
        return "API xato"


# ===== START =====
async def start(update, context):
    chat_id = update.effective_chat.id

    # 🔥 ADMIN avtomatik qo‘shiladi
    ADMINS.add(chat_id)

    keyboard = [
        ["📊 Umumiy", "⚡ Real-time"],
        ["👨‍💼 Hodimlar"]
    ]

    await update.message.reply_text(
        "Bot ishlayapti 👌\nSiz admin sifatida qo‘shildingiz",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# ===== HANDLE =====
async def handle(update, context):
    text = update.message.text

    if text == "📊 Umumiy":
        await update.message.reply_text(get_data("umumiy"))

    elif text == "⚡ Real-time":
        await update.message.reply_text(get_data("realtime"))

    elif text == "👨‍💼 Hodimlar":
        await update.message.reply_text(get_data("hodimlar"))


# ===== ADMIN BROADCAST =====
async def send_all(update, context):
    chat_id = update.effective_chat.id

    if chat_id not in ADMINS:
        await update.message.reply_text("❌ Siz admin emassiz")
        return

    msg = " ".join(context.args)

    for admin in ADMINS:
        try:
            await context.bot.send_message(admin, msg)
        except:
            pass


# ===== MAIN =====
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_all))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("Bot ishlayapti...")

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
