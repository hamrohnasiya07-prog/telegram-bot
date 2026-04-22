import requests
import pandas as pd
import os
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from datetime import datetime, timedelta, time

from concurrent.futures import ThreadPoolExecutor
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill

# ======================
TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

ADMINS = set()
state = {}

# ======================
# SERVER (Railway)
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

    df.columns = [
        "Hodim","Mijoz","Qo‘ng‘iroq","Muxlat",
        "To‘lov","Kechikdi","Bog‘lanmadi","Muamoli","Sud"
    ]

    df.to_excel(filename, index=False)

    wb = load_workbook(filename)
    ws = wb.active

    # HEADER STYLE
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")

    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center")
        cell.fill = header_fill

    # ZEBRA STYLE
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        if row[0].row % 2 == 0:
            for cell in row:
                cell.fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")

    # AUTO WIDTH
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter

        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 4

    wb.save(filename)

    await bot.send_document(chat_id=chat_id, document=open(filename, "rb"))
    os.remove(filename)

# ======================
async def auto_report(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")
    d = get(API_URL + "?type=today")

    for chat_id in ADMINS:
        try:
            await context.bot.send_message(chat_id, fmt(d, f"📅 AUTO ({today})"))
        except:
            pass

# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ADMINS.add(chat_id)
    state[chat_id] = None

    kb = [
        ["📊 Umumiy","⚡ Real-time"],
        ["👤 Hodimlar","📊 Barcha hodimlar"]
    ]

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

    if txt == "📊 Umumiy":
        await update.message.reply_text(fmt(get(API_URL+"?type=all"),"UMUMIY"))
        return

    if txt == "⚡ Real-time":
        await update.message.reply_text(fmt(get(API_URL+"?type=today"),"REAL-TIME"))
        return

    if txt == "⬅️ Ortga":
        await start(update, context)
        return

    if txt == "👤 Hodimlar":
        kb = [HODIMLAR[i:i+3] for i in range(0,len(HODIMLAR),3)]
        kb.append(["⬅️ Ortga"])
        state[chat] = "hodim"
        await update.message.reply_text("Hodim tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if txt == "📊 Barcha hodimlar":
        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        state[chat] = {"mode":"all"}
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    # ===== OYLIK =====
    if isinstance(state.get(chat), dict) and state[chat].get("mode") == "all":

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
            today = datetime.now()
            kb = [[(today - timedelta(days=i)).strftime("%Y-%m-%d")] for i in range(5)]
            kb.append(["⬅️ Ortga"])
            state[chat]["mode"] = "all_day"
            await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

    # ===== KUNLIK =====
    if isinstance(state.get(chat), dict) and state[chat].get("mode") == "all_day":

        if not txt.startswith("202"):
            return

        urls = [API_URL + f"?type=day&date={txt}&hodim={h}" for h in HODIMLAR]
        results = get_many(urls)

        rows = []
        for i, d in enumerate(results):
            if d:
                rows.append({"Hodim": HODIMLAR[i], **d})

        if not rows:
            await update.message.reply_text("❌ Ma'lumot yo‘q")
            return

        await send_excel(context.bot, rows, f"{txt}.xlsx", chat)
        return

    # ===== HODIM TANLASH =====
    if state.get(chat) == "hodim":
        state[chat] = {"hodim": txt}
        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    # ===== HODIM MODE =====
    if isinstance(state.get(chat), dict) and "hodim" in state[chat]:

        h = state[chat]["hodim"]

        if txt == "📆 Oylik":
            await update.message.reply_text(fmt(get(API_URL+f"?type=hodim_oy&hodim={h}"),f"{h} (oy)"))
            return

        if txt == "📅 Kunlik":
            today = datetime.now()
            kb = [[(today - timedelta(days=i)).strftime("%Y-%m-%d")] for i in range(5)]
            kb.append(["⬅️ Ortga"])
            state[chat]["mode"] = "day"
            await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

        if state[chat].get("mode") == "day":
            await update.message.reply_text(
                fmt(get(API_URL+f"?type=day&date={txt}&hodim={h}"),f"{h} ({txt})")
            )
            return

# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.job_queue.run_daily(auto_report, time=time(hour=18, minute=10))

print("Bot ishlayapti...")
app.run_polling()
