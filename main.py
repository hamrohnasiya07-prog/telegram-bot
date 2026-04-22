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
TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
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
def safe(d):
    if not d:
        return {
            "mijoz":0,"qongiroq":0,"muxlat":0,
            "tolov":0,"kechikdi":0,"bog":0,
            "muamoli":0,"sud":0
        }
    return d

def get(url):
    try:
        r = requests.get(url, timeout=4)
        return safe(r.json()) if r.status_code == 200 else safe(None)
    except:
        return safe(None)

def get_many(urls):
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(get, urls))

# ======================
def fmt(d, title):
    d = safe(d)
    return (
        f"📊 {title}\n\n"
        f"👥 Mijozlar: {d['mijoz']}\n"
        f"📞 Qo‘ng‘iroq: {d['qongiroq']}\n"
        f"📅 Muxlat: {d['muxlat']}\n"
        f"💰 To‘lov: {d['tolov']}\n"
        f"⏰ Kechikdi: {d['kechikdi']}\n"
        f"📵 Bog‘lanmadi: {d['bog']}\n"
        f"⚠️ Muamoli: {d['muamoli']}\n"
        f"⚖️ Sud: {d['sud']}"
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

    if not txt:
        return

    s = state.get(chat, {"flow":"menu"})

    # ===== MENU =====
    if txt == "⬅️ Ortga":
        return await start(update, context)

    if txt == "📊 Umumiy":
        return await update.message.reply_text(fmt(get(API_URL+"?type=all"),"UMUMIY"))

    if txt == "⚡ Real-time":
        return await update.message.reply_text(fmt(get(API_URL+"?type=today"),"REAL-TIME"))

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
            return await update.message.reply_text(fmt(get(API_URL+f"?type=hodim_oy&hodim={h}"),f"{h} (oy)"))

        if txt == "📅 Kunlik":
            dates = [(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            kb = [[d] for d in dates]
            kb.append(["⬅️ Ortga"])

            state[chat]["flow"] = "hodim_day"
            return await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if s["flow"] == "hodim_day":
        h = s["hodim"]
        return await update.message.reply_text(fmt(get(API_URL+f"?type=day&date={txt}&hodim={h}"),f"{h} ({txt})"))

    # ===== BARCHA =====
    if txt == "📊 Barcha hodimlar":
        state[chat] = {"flow":"all_menu"}

        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        return await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if s["flow"] == "all_menu":

        if txt == "📆 Oylik":

            urls = [API_URL+f"?type=hodim_oy&hodim={h}" for h in HODIMLAR]
            data = get_many(urls)

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
        data = get_many(urls)

        rows = [{"Hodim":HODIMLAR[i], **data[i]} for i in range(len(data))]

        return await send_excel(context.bot, rows, f"{txt}.xlsx", chat)

# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot ishlayapti...")
app.run_polling()
