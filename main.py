from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup
import requests
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

USERS = set()

# ===== Render uchun server =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server).start()
# =================================


def start(update, context):
    chat_id = update.effective_chat.id
    USERS.add(chat_id)

    keyboard = [["📊 Umumiy", "⚡ Real-time"]]

    update.message.reply_text(
        "Bot ishlayapti 👌",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


def handle(update, context):
    text = update.message.text

    if text == "📊 Umumiy":
        update.message.reply_text("Umumiy ishladi ✅")

    elif text == "⚡ Real-time":
        update.message.reply_text("Realtime ishladi ✅")


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle))

    print("Bot ishlayapti...")

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
