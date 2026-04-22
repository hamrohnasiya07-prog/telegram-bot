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
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

def get_many(urls):
    with ThreadPoolExecutor(max_workers=10) as executor:
        return list(executor.map(get, urls))

# ======================
def safe(d):
    if not d:
        return {
            "mijoz":0,"qongiroq":0,"muxlat":0,
            "tolov":0,"kechikdi":0,"bog":0,
            "muamoli":0,"sud":0
        }
    return d

def fmt(d, title):
    d = safe(d)
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
async def send_excel(bot, rows, filename, chat_id):

    df = pd.DataFrame(rows)

    df.columns = [
        "Hodim","Mijoz","Qo‘ng‘iroq","Muxlat",
        "To‘lov","Kechikdi","Bog‘lanmadi","Muamoli","Sud"
    ]

    df.to_excel(filename, index=False)

    wb = load_workbook(filename)
    ws = wb.active

    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")

    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center")
        cell.fill = header_fill

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        if row[0].row % 2 == 0:
            for cell in row:
                cell.fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ADMINS.add(chat_id)
    state[chat_id] = {}

    kb = [
        ["📊 Umumiy","⚡ Real-time"],
        ["👤 Hodimlar","📊 Barcha hodimlar"]
    ]

    await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# ======================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = update.message.text
    chat = update.effective_chat.id
    s = state.get(chat, {})

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

    # ===== HODIM =====
    if txt == "👤 Hodimlar":
        kb = [HODIMLAR[i:i+3] for i in range(0,len(HODIMLAR),3)]
        kb.append(["⬅️ Ortga"])
        state[chat] = {"type":"hodim"}
        await update.message.reply_text("Hodim tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if s.get("type") == "hodim" and "hodim" not in s:
        state[chat]["hodim"] = txt
        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if s.get("type") == "hodim" and txt == "📅 Kunlik":

        # 🔥 16 sanadan boshlab
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(0, 10)]
        dates = sorted(dates)  # eski → yangi

        kb = [[d] for d in dates]
        kb.append(["⬅️ Ortga"])

        state[chat]["mode"] = "day"

        await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if s.get("mode") == "day":
        h = s.get("hodim")

        d = safe(get(API_URL+f"?type=day&date={txt}&hodim={h}"))

        await update.message.reply_text(fmt(d, f"{h} ({txt})"))
        return

# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot ishlayapti...")
app.run_polling()
