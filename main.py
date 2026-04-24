import aiohttp
import asyncio
import pandas as pd
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from datetime import datetime, timedelta

TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

USERS = {}

# ======================
def safe(d):
    base = {
        "mijoz":0,"qongiroq":0,"muxlat":0,
        "tolov":0,"muamoli":0,"sud":0,"bog":0
    }
    if not d:
        return base
    for k in base:
        if k not in d:
            d[k] = 0
    return d

# ======================
async def api(params):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(API_URL, params=params, timeout=7) as r:
                return await r.json()
    except:
        return None

# ======================
def fmt(d, title):
    d = safe(d)
    return (
        f"📊 {title}\n\n"
        f"👥 Mijoz: {d['mijoz']}\n"
        f"📞 Qo‘ng‘iroq: {d['qongiroq']}\n"
        f"💰 To‘lov: {d['tolov']}\n"
        f"📅 Muxlat: {d['muxlat']}\n"
        f"⚖️ Sud: {d['sud']}\n"
        f"🚫 Bog‘lanmadi: {d['bog']}\n"
        f"⚠️ Muamoli: {d['muamoli']}"
    )

# ======================
async def send_excel(bot, rows, filename, chat_id):
    if not rows:
        return await bot.send_message(chat_id, "❌ Ma'lumot topilmadi")

    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)

    await bot.send_document(chat_id=chat_id, document=open(filename, "rb"))
    os.remove(filename)

# ======================
def dates():
    return [(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USERS[update.effective_chat.id] = {"step":"menu"}

    kb = [
        ["📊 Umumiy"],
        ["📅 Kunlik hisobot"]
    ]

    await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# ======================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat.id
    text = update.message.text
    user = USERS.get(chat, {"step":"menu"})

    if text == "📊 Umumiy":
        d = await api({"type":"all"})
        return await update.message.reply_text(fmt(d,"UMUMIY"))

    # ======================
    # 📅 KUNLIK HISOBOT
    if text == "📅 Kunlik hisobot":
        USERS[chat] = {"step":"date"}
        kb = [[d] for d in dates()]
        return await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if user["step"] == "date":

        date = text

        d = await api({"type":"daily_summary","date":date})
        top = await api({"type":"top","date":date})
        rows = await api({"type":"employees_daily_excel","date":date})

        msg = fmt(d, f"KUNLIK ({date})")

        if top and top.get("hodim"):
            msg += f"\n\n🏆 TOP: {top['hodim']} ({top['tolov']})"

        await update.message.reply_text(msg)

        return await send_excel(context.bot, rows, f"kunlik_{date}.xlsx", chat)

# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT ISHLAYAPTI")
app.run_polling()
