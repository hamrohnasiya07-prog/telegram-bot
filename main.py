import requests
import pandas as pd
from datetime import datetime, time
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

# ===== RENDER KEEP-ALIVE =====
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
# =============================

TOKEN = "8547255151:AAEy3ZZOCFTNlsCd943vrQsFOKKMsH497d0"
API_URL = "https://script.google.com/macros/s/AKfycbyRa-vQ2Q8H0lbnjD1aPXHFhpr682QmShcm_JDQCF777Jj37UyNJEGM2tTJ7rGpTmOr/exec"

USERS = set()

HODIMLAR = [
    "Layla","Zufarbek","Nazokat","Bibizaxro",
    "Moxinur","Abdurasul","Uzipa","Aziza",
    "Jo'rabek","Shukrjon","Nilufar","Otabek"
]

# ======================
def get(url):
    try:
        return requests.get(url, timeout=5).json()
    except:
        return None

# ======================
def fmt(d, title):
    if not d:
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
def send_excel(bot, rows, filename, chat_id):
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    bot.send_document(chat_id=chat_id, document=open(filename, "rb"))

# ======================
def auto_report(context):
    bot = context.bot
    today = datetime.now().strftime("%Y-%m-%d")

    d = get(API_URL + "?type=today")

    for chat_id in USERS:
        try:
            bot.send_message(chat_id=chat_id, text=fmt(d, f"📅 AUTO ({today})"))
        except:
            pass

    rows = []

    for h in HODIMLAR:
        d = get(API_URL + f"?type=day&date={today}&hodim={h}")
        if d:
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
            send_excel(bot, rows, f"hisobot_{today}.xlsx", chat_id)
        except:
            pass

# ======================
def start(update, context):
    chat_id = update.effective_chat.id
    USERS.add(chat_id)

    kb = [
        ["📊 Umumiy","⚡ Real-time"],
        ["👤 Hodimlar","📊 Barcha hodimlar"]
    ]

    update.message.reply_text(
        "Tanlang:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

# ======================
def handle(update, context):
    txt = update.message.text
    chat = update.effective_chat.id

    if txt == "📊 Umumiy":
        update.message.reply_text(fmt(get(API_URL+"?type=all"),"UMUMIY"))
        return

    if txt == "⚡ Real-time":
        update.message.reply_text(fmt(get(API_URL+"?type=today"),"REAL-TIME"))
        return

    if txt == "👤 Hodimlar":
        kb = [HODIMLAR[i:i+3] for i in range(0,len(HODIMLAR),3)]
        kb.append(["⬅️ Ortga"])
        context.user_data["state"] = "hodim"
        update.message.reply_text("Tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if txt == "⬅️ Ortga":
        start(update, context)
        return

    if context.user_data.get("state") == "hodim":
        update.message.reply_text(
            fmt(get(API_URL+f"?type=hodim_oy&hodim={txt}"),f"{txt} (oy)")
        )

# ======================
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle))

    # AUTO REPORT (18:10)
    updater.job_queue.run_daily(auto_report, time(hour=18, minute=10))

    print("Bot ishlayapti...")
    updater.start_polling()
    updater.idle()

# ======================
if __name__ == "__main__":
    main()
