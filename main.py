import aiohttp
import asyncio
import pandas as pd
import os
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from datetime import datetime, timedelta

TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

state = {}

# ======================
# KEEP ALIVE (Railway)
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
def safe(d):
    base = {
        "mijoz":0,
        "qongiroq":0,
        "muxlat":0,
        "tolov":0,
        "kechikdi":0,
        "bog":0,
        "muamoli":0,
        "sud":0
    }

    if not d:
        return base

    for k in base:
        if k not in d:
            d[k] = 0

    return d

# ======================
async def fetch(session, url):
    try:
        async with session.get(url, timeout=5) as res:
            data = await res.json()
            return safe(data)
    except:
        return safe(None)

async def get_many(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, u) for u in urls]
        return await asyncio.gather(*tasks)

# ======================
def fmt(d, title):
    d = safe(d)

    return (
        f"📊 {title}\n\n"
        f"👥 {d['mijoz']} | 📞 {d['qongiroq']} ta | 💰 {d['tolov']} so‘m\n"
        f"📅 {d['muxlat']} kun | ⚖️ {d['sud']} ta\n"
        f"⏰ {d['kechikdi']} | 🚫 {d['bog']} | ⚠️ {d['muamoli']}"
    )

# ======================
async def send_excel(bot, rows, filename, chat_id):
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    await bot.send_document(chat_id=chat_id, document=open(filename, "rb"))
    os.remove(filename)

# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    state[chat] = {"flow": "menu"}

    kb = [
        ["📊 Umumiy","⚡ Real-time"],
        ["👤 Hodimlar","📊 Barcha hodimlar"]
    ]

    await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# ======================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = update.message.text
    chat = update.effective_chat.id
    s = state.get(chat, {"flow":"menu"})

    if not txt:
        return

    if txt == "⬅️ Ortga":
        return await start(update, context)

    # ===== UMUMIY =====
    if txt == "📊 Umumiy":
        async with aiohttp.ClientSession() as session:
            d = await fetch(session, API_URL+"?type=all")
        return await update.message.reply_text(fmt(d, "UMUMIY"))

    if txt == "⚡ Real-time":
        async with aiohttp.ClientSession() as session:
            d = await fetch(session, API_URL+"?type=today")
        return await update.message.reply_text(fmt(d, "REAL-TIME"))

    # ===== HODIMLAR =====
    if txt == "👤 Hodimlar":
        state[chat] = {"flow":"hodim_list"}

        kb = [HODIMLAR[i:i+3] for i in range(0,len(HODIMLAR),3)]
        kb.append(["⬅️ Ortga"])

        return await update.message.reply_text("Hodim tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if s["flow"] == "hodim_list":
        state[chat] = {"flow":"hodim_menu","hodim":txt}

        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        return await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if s["flow"] == "hodim_menu":

        h = s["hodim"]

        if txt == "📆 Oylik":
            async with aiohttp.ClientSession() as session:
                d = await fetch(session, API_URL+f"?type=hodim_oy&hodim={h}")
            return await update.message.reply_text(fmt(d, f"{h}"))

        if txt == "📅 Kunlik":
            dates = [(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            kb = [[d] for d in dates]
            kb.append(["⬅️ Ortga"])

            state[chat]["flow"] = "hodim_day"
            return await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if s["flow"] == "hodim_day":
        h = s["hodim"]

        async with aiohttp.ClientSession() as session:
            d = await fetch(session, API_URL+f"?type=day&date={txt}&hodim={h}")

        return await update.message.reply_text(fmt(d, f"{h} ({txt})"))

    # ===== BARCHA =====
    if txt == "📊 Barcha hodimlar":
        state[chat] = {"flow":"all"}

        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        return await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if s["flow"] == "all":

        if txt == "📆 Oylik":
            urls = [API_URL+f"?type=hodim_oy&hodim={h}" for h in HODIMLAR]
            data = await get_many(urls)

            rows = [{"Hodim":HODIMLAR[i], **data[i]} for i in range(len(data))]
            return await send_excel(context.bot, rows, "oylik.xlsx", chat)

        if txt == "📅 Kunlik":
            dates = [(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            kb = [[d] for d in dates]
            kb.append(["⬅️ Ortga"])

            state[chat]["flow"] = "all_day"
            return await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if s["flow"] == "all_day":
        urls = [API_URL+f"?type=day&date={txt}&hodim={h}" for h in HODIMLAR]
        data = await get_many(urls)

        rows = [{"Hodim":HODIMLAR[i], **data[i]} for i in range(len(data))]
        return await send_excel(context.bot, rows, f"{txt}.xlsx", chat)

# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot ishlayapti...")
app.run_polling()
