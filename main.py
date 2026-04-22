import requests
import pandas as pd
import os
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from datetime import datetime, timedelta, time

# ======================
# CONFIG
# ======================
TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

state = {}

# ======================
# RAILWAY SERVER
# ======================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ======================
# HODIMLAR
# ======================
HODIMLAR = [
    "Layla","Zufarbek","Nazokat","Bibizaxro",
    "Moxinur","Abdurasul","Uzipa","Aziza",
    "Jo'rabek","Shukurjan","Nilufar","Otabek"
]

# ======================
# API
# ======================
def get(url):
    try:
        return requests.get(url, timeout=5).json()
    except:
        return None

# ======================
# FORMAT
# ======================
def fmt(d, title):
    if not d:
        return "❌ Xatolik"

    return f"""
📊 {title}

👥 Mijozlar: {d['mijoz']}
📞 Qo‘ng‘iroq: {d['qongiroq']}
📅 Muxlat: {d['muxlat']}
💰 To‘lov: {d['tolov']}
⏰ Kechikdi: {d['kechikdi']}
📵 Bog‘lanmadi: {d['bog']}
⚠️ Muamoli: {d['muamoli']}
⚖️ Sud: {d['sud']}
"""

# ======================
# EXCEL
# ======================
async def send_excel(bot, rows, filename, chat_id):
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    await bot.send_document(chat_id=chat_id, document=open(filename, "rb"))
    os.remove(filename)

# ======================
# AUTO REPORT (FIXED)
# ======================
async def auto_report(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")

    d = get(API_URL + "?type=today")

    # 🔥 barcha aktiv userlarga yuboradi
    for chat_id in context.application.chat_data.keys():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=fmt(d, f"📅 AUTO HISOBOT ({today})")
            )
        except:
            pass

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # 🔥 userni saqlaymiz (DB o‘rniga)
    context.application.chat_data[chat_id] = True

    kb = [
        ["📊 Umumiy","⚡ Real-time"],
        ["👤 Hodimlar","📊 Barcha hodimlar"]
    ]

    await update.message.reply_text(
        "Tanlang:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

# ======================
# HANDLER
# ======================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = update.message.text
    chat = update.effective_chat.id

    if txt == "📊 Umumiy":
        await update.message.reply_text(fmt(get(API_URL+"?type=all"),"UMUMIY"))
        return

    if txt == "⚡ Real-time":
        await update.message.reply_text(fmt(get(API_URL+"?type=today"),"REAL-TIME"))
        return

    if txt == "📊 Barcha hodimlar":
        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        state[chat] = "all"
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if state.get(chat) == "all":

        if txt == "📆 Oylik":
            rows = []

            for h in HODIMLAR:
                d = get(API_URL+f"?type=hodim_oy&hodim={h}")
                if d:
                    rows.append(d)

            if not rows:
                await update.message.reply_text("❌ Ma'lumot yo‘q")
                return

            await send_excel(context.bot, rows, "oylik.xlsx", chat)
            return

# ======================
# RUN
# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))

app.job_queue.run_daily(auto_report, time=time(hour=18, minute=10))

print("Bot ishlayapti...")
app.run_polling()
