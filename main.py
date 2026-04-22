import requests
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta, time

# ====== RENDER PORT FIX (BEPUL WORKAROUND) ======
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running')

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server).start()
# ===============================================

TOKEN = "8723725408:AAH0HmdADqcWmHdKWm2BfrGl7uOk2SvffIc"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

state = {}
USERS = set()  # 🔥 avtomatik userlar

HODIMLAR = [
    "Layla","Zufarbek","Nazokat","Bibizaxro",
    "Moxinur","Abdurasul","Uzipa","Aziza",
    "Jo'rabek","Shukrjon","Nilufar","Otabek"
]

# ======================
# API
# ======================
def get(url):
    try:
        return requests.get(url, timeout=5).json()
    except Exception as e:
        print("API ERROR:", e)
        return None

# ======================
# FORMAT
# ======================
def fmt(d, title):
    if not d or not isinstance(d, dict):
        return "❌ Ma'lumot topilmadi"

    return f"""
📊 {title}

👥 Mijozlar: {d.get('mijoz',0)}
📞 Qo‘ng‘iroq: {d.get('qongiroq',0)}
📅 Muxlat: {d.get('muxlat',0)}
💰 To‘lov: {d.get('tolov',0)}
⏰ Kechikdi: {d.get('kechikdi',0)}
📵 Bog‘lanmadi: {d.get('bog',0)}
⚠️ Muamoli: {d.get('muamoli',0)}
⚖️ Sud: {d.get('sud',0)}
"""

# ======================
# EXCEL
# ======================
async def send_excel(bot, rows, filename, chat_id):
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    await bot.send_document(chat_id=chat_id, document=open(filename, "rb"))

# ======================
# AUTO REPORT
# ======================
async def auto_report(context: ContextTypes.DEFAULT_TYPE):

    today = datetime.now().strftime("%Y-%m-%d")

    d = get(API_URL + "?type=today")

    # 🔥 TEXT HAMMAGA
    for chat_id in USERS:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=fmt(d, f"📅 AUTO HISOBOT ({today})")
            )
        except Exception as e:
            print("SEND ERROR:", e)

    # 🔥 EXCEL
    rows = []

    for h in HODIMLAR:
        d = get(API_URL + f"?type=day&date={today}&hodim={h}")
        if d is not None:
            rows.append({
                "Hodim": h,
                "Mijoz": d["mijoz"],
                "Qongiroq": d["qongiroq"],
                "Muxlat": d["muxlat"],
                "Tolov": d["tolov"],
                "Kechikdi": d["kechikdi"],
                "Boglanmadi": d["bog"],
                "Muamoli": d["muamoli"],
                "Sud": d["sud"]
            })

    for chat_id in USERS:
        try:
            await send_excel(context.bot, rows, f"hisobot_{today}.xlsx", chat_id)
        except Exception as e:
            print("EXCEL ERROR:", e)

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    USERS.add(chat_id)  # 🔥 USER QO‘SHILDI

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

    if txt == "👤 Hodimlar":
        kb = [HODIMLAR[i:i+3] for i in range(0,len(HODIMLAR),3)]
        kb.append(["⬅️ Ortga"])
        state[chat] = "hodim"
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if txt == "⬅️ Ortga":
        await start(update, context)
        return

    if state.get(chat) == "hodim":
        await update.message.reply_text(
            fmt(get(API_URL+f"?type=hodim_oy&hodim={txt}"),f"{txt} (oy)")
        )
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
