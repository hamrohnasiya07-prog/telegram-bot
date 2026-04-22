import requests
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta, time

# ======================
# CONFIG
# ======================
TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

# 🔥 ADMINLAR (avtomatik yig'iladi)
ADMINS = set()

# ===== Railway server =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ==========================

state = {}

# 🔥 MUHIM — SHEETS NOMIGA 100% MOS BO‘LSIN
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

# ======================
# AUTO REPORT
# ======================
async def auto_report(context: ContextTypes.DEFAULT_TYPE):

    today = datetime.now().strftime("%Y-%m-%d")

    d = get(API_URL + "?type=today")
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=fmt(d, f"📅 AUTO HISOBOT ({today})")
    )

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

    if rows:
        await send_excel(context.bot, rows, f"hisobot_{today}.xlsx", CHAT_ID)

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        ["📊 Umumiy","⚡ Real-time"],
        ["👤 Hodimlar","📊 Barcha hodimlar"]
    ]
    await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# ======================
# HANDLER
# ======================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = update.message.text
    chat = update.effective_chat.id

    # UMUMIY
    if txt == "📊 Umumiy":
        await update.message.reply_text(fmt(get(API_URL+"?type=all"),"UMUMIY"))
        return

    # REAL TIME
    if txt == "⚡ Real-time":
        await update.message.reply_text(fmt(get(API_URL+"?type=today"),"REAL-TIME"))
        return

    # BARCHA HODIMLAR
    if txt == "📊 Barcha hodimlar":
        kb = [["📆 Oylik","📅 Kunlik"],["⬅️ Ortga"]]
        state[chat] = "all"
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    # ALL MODE
    if state.get(chat) == "all":

        # OYLIK → EXCEL
        if txt == "📆 Oylik":

            rows = []

            for h in HODIMLAR:
                d = get(API_URL+f"?type=hodim_oy&hodim={h}")
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

            if not rows:
                await update.message.reply_text("❌ Ma'lumot topilmadi")
                return

            await send_excel(context.bot, rows, "oylik.xlsx", chat)
            return

        # KUNLIK
        if txt == "📅 Kunlik":
            today = datetime.now()
            kb = [[(today - timedelta(days=i)).strftime("%Y-%m-%d")] for i in range(5)]
            kb.append(["⬅️ Ortga"])
            state[chat] = {"mode":"all_day"}
            await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

    # ALL DAY → EXCEL
    if isinstance(state.get(chat), dict) and state[chat].get("mode") == "all_day":

        if txt == "⬅️ Ortga":
            await start(update, context)
            return

        rows = []

        for h in HODIMLAR:
            d = get(API_URL+f"?type=day&date={txt}&hodim={h}")
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

        if not rows:
            await update.message.reply_text("❌ Ma'lumot topilmadi")
            return

        await send_excel(context.bot, rows, f"kunlik_{txt}.xlsx", chat)
        return

    # HODIMLAR
    if txt == "👤 Hodimlar":
        kb = [HODIMLAR[i:i+3] for i in range(0,len(HODIMLAR),3)]
        kb.append(["⬅️ Ortga"])
        state[chat] = "hodim"
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    # ORTGA
    if txt == "⬅️ Ortga":
        await start(update, context)
        return

    # HODIM TANLANDI
    if state.get(chat) == "hodim":
        state[chat] = {"hodim":txt}
        kb = [["📅 Kunlik","📆 Oylik"],["⬅️ Ortga"]]
        await update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    # HODIM LOGIKA
    if isinstance(state.get(chat), dict):
        h = state[chat]["hodim"]

        if txt == "📆 Oylik":
            await update.message.reply_text(fmt(get(API_URL+f"?type=hodim_oy&hodim={h}"),f"{h} (oy)"))
            return

        if txt == "📅 Kunlik":
            today = datetime.now()
            kb = [[(today - timedelta(days=i)).strftime("%Y-%m-%d")] for i in range(5)]
            kb.append(["⬅️ Ortga"])
            state[chat]["mode"]="day"
            await update.message.reply_text("Sanani tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

        if state[chat].get("mode") == "day":
            await update.message.reply_text(
                fmt(get(API_URL+f"?type=day&date={txt}&hodim={h}"),f"{h} ({txt})")
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
