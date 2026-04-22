import requests
import pandas as pd
import os
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from datetime import datetime, timedelta

from concurrent.futures import ThreadPoolExecutor

# ======================
TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0    "
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

state = {}

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
HODIMLAR = [
    "Layla","Zufarbek","Nazokat","Bibizaxro",
    "Moxinur","Abdurasul","Uzipa","Aziza",
    "Jo'rabek","Shukurjan","Nilufar","Otabek"
]

# ======================
def get(url):
    try:
        return requests.get(url, timeout=5).json()
    except:
        return None

def get_many(urls):
    with ThreadPoolExecutor(max_workers=10) as executor:
        return list(executor.map(get, urls))

# ======================
def fmt(d, title):
    if not d:
        return "❌ Xatolik"

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
async def send_excel(bot, rows, filename, chat_id):
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    await bot.send_document(chat_id=chat_id, document=open(filename, "rb"))
    os.remove(filename)

# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kb = [
        ["📊 Umumiy","⚡ Real-time"],
        ["👤 Hodimlar","📊 Barcha hodimlar"]
    ]

    state[update.effective_chat.id] = {}

    await update.message.reply_text(
        "Tanlang:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

# ======================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = update.message.text
    chat = update.effective_chat.id

    if not txt:
        return

    # =================
    # UMUMIY
    # =================
    if txt == "📊 Umumiy":
        await update.message.reply_text(fmt(get(API_URL+"?type=all"),"UMUMIY"))
        return

    if txt == "⚡ Real-time":
        await update.message.reply_text(fmt(get(API_URL+"?type=today"),"REAL-TIME"))
        return

    if txt == "⬅️ Ortga":
        await start(update, context)
        return

    # =================
    # BARCHA HODIMLAR
    # =================
    if txt == "📊 Barcha hodimlar":
        state[chat] = {"flow": "all"}
        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    s = state.get(chat, {})

    if s.get("flow") == "all":

        if txt == "📆 Oylik":
            urls = [API_URL + f"?type=hodim_oy&hodim={h}" for h in HODIMLAR]
            results = get_many(urls)

            rows = []
            for i, d in enumerate(results):
                if d:
                    rows.append({"Hodim": HODIMLAR[i], **d})

            await send_excel(context.bot, rows, "oylik.xlsx", chat)
            return

        if txt == "📅 Kunlik":
            dates = [(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)]
            kb = [[d] for d in dates]
            kb.append(["⬅️ Ortga"])

            state[chat]["flow"] = "all_day"

            await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

    if s.get("flow") == "all_day":

        urls = [API_URL + f"?type=day&date={txt}&hodim={h}" for h in HODIMLAR]
        results = get_many(urls)

        rows = []
        for i, d in enumerate(results):
            if d:
                rows.append({"Hodim": HODIMLAR[i], **d})

        await send_excel(context.bot, rows, f"{txt}.xlsx", chat)
        return

# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot ishlayapti...")
app.run_polling()
