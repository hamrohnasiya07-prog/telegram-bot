import aiohttp
import asyncio
import pandas as pd
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from datetime import datetime, timedelta

TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

# ======================
USERS = {}   # chat_id -> {step, hodim, mode, date}

HODIMLAR = [
    "Layla","Zufarbek","Nazokat","Bibizaxro",
    "Moxinur","Abdurasul","Uzipa","Aziza",
    "Jo'rabek","Shukurjan","Nilufar","Otabek"
]

# ======================
def safe(d):
    base = {
        "mijoz":0,"qongiroq":0,"tolov":0,
        "muxlat":0,"sud":0,"kechikdi":0,
        "bog":0,"muamoli":0
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
            async with s.get(API_URL, params=params, timeout=6) as r:
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
        f"⏰ Kechikdi: {d['kechikdi']}\n"
        f"🚫 Bog‘lanmadi: {d['bog']}\n"
        f"⚠️ Muamoli: {d['muamoli']}"
    )

# ======================
async def send_excel(bot, rows, filename, chat_id):
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    await bot.send_document(chat_id=chat_id, document=open(filename, "rb"))
    os.remove(filename)

# ======================
def main_menu():
    return ReplyKeyboardMarkup([
        ["📊 Umumiy"],
        ["📅 Kunlik hisobot"],
        ["👤 Xodimlar","📊 Barcha xodimlar"]
    ], resize_keyboard=True)

def back_kb():
    return ReplyKeyboardMarkup([["⬅️ Ortga"]], resize_keyboard=True)

# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    USERS[chat] = {"step":"menu"}
    await update.message.reply_text("Tanlang:", reply_markup=main_menu())

# ======================
def last_dates(n=7):
    return [(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]

# ======================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    text = update.message.text
    u = USERS.get(chat, {"step":"menu"})

    if text == "⬅️ Ortga":
        USERS[chat] = {"step":"menu"}
        return await update.message.reply_text("Tanlang:", reply_markup=main_menu())

    # ===== UMUMIY (o‘zgarmaydi) =====
    if text == "📊 Umumiy":
        d = await api({"type":"all"})
        return await update.message.reply_text(fmt(d,"UMUMIY"))

    # ===== YANGI: KUNLIK HISOBOT (O ustun bo‘yicha) =====
    if text == "📅 Kunlik hisobot":
        USERS[chat] = {"step":"daily_pick_date"}
        kb = [[d] for d in last_dates(10)] + [["⬅️ Ortga"]]
        return await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if u["step"] == "daily_pick_date":
        date = text
        # umumiy kunlik summary
        d = await api({"type":"daily_summary","date":date})
        # barcha xodimlar bo‘yicha Excel (faqat O ustunda sana bor yozuvlar)
        rows = await api({"type":"employees_daily_excel","date":date}) or []
        await update.message.reply_text(fmt(d, f"KUNLIK ({date})"))
        return await send_excel(context.bot, rows, f"kunlik_{date}.xlsx", chat)

    # ===== BARCHA XODIMLAR (faqat Excel) =====
    if text == "📊 Barcha xodimlar":
        USERS[chat] = {"step":"all_menu"}
        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        return await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if u["step"] == "all_menu":
        if text == "📆 Oylik":
            rows = await api({"type":"employees_month_excel"}) or []
            return await send_excel(context.bot, rows, "barcha_oylik.xlsx", chat)

        if text == "📅 Kunlik":
            USERS[chat] = {"step":"all_day_pick"}
            kb = [[d] for d in last_dates(10)] + [["⬅️ Ortga"]]
            return await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if u["step"] == "all_day_pick":
        date = text
        rows = await api({"type":"employees_daily_excel","date":date}) or []
        return await send_excel(context.bot, rows, f"barcha_{date}.xlsx", chat)

    # ===== XODIMLAR =====
    if text == "👤 Xodimlar":
        USERS[chat] = {"step":"emp_pick"}
        kb = [HODIMLAR[i:i+3] for i in range(0,len(HODIMLAR),3)] + [["⬅️ Ortga"]]
        return await update.message.reply_text("Xodim tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if u["step"] == "emp_pick":
        USERS[chat] = {"step":"emp_range","hodim":text.strip()}
        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        return await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if u["step"] == "emp_range":
        if text == "📆 Oylik":
            USERS[chat]["step"] = "emp_view"
            USERS[chat]["range"] = "month"
            kb = [["📋 Jadval","📄 Excel"],["⬅️ Ortga"]]
            return await update.message.reply_text("Ko‘rish turini tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

        if text == "📅 Kunlik":
            USERS[chat]["step"] = "emp_day_pick"
            kb = [[d] for d in last_dates(10)] + [["⬅️ Ortga"]]
            return await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if u["step"] == "emp_day_pick":
        USERS[chat]["step"] = "emp_view"
        USERS[chat]["range"] = "day"
        USERS[chat]["date"] = text
        kb = [["📋 Jadval","📄 Excel"],["⬅️ Ortga"]]
        return await update.message.reply_text("Ko‘rish turini tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    if u["step"] == "emp_view":
        h = u["hodim"]
        r = u["range"]
        date = u.get("date")

        if text == "📋 Jadval":
            params = {"type":"employee_summary","hodim":h,"range":r}
            if r == "day":
                params["date"] = date
            d = await api(params)
            title = f"{h} ({'oy' if r=='month' else date})"
            return await update.message.reply_text(fmt(d, title))

        if text == "📄 Excel":
            params = {"type":"employee_excel","hodim":h,"range":r}
            if r == "day":
                params["date"] = date
            rows = await api(params) or []
            fname = f"{h}_{'oylik' if r=='month' else date}.xlsx"
            return await send_excel(context.bot, rows, fname, chat)

# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot ishga tushdi")
app.run_polling()
