import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ================= CONFIG =================
TOKEN = "8731071318:AAHdKplit0Ods2zt42oAyyNgldRPo5BXlbg"
SHEET_NAME = "HISOBOT"

# ================= GOOGLE SHEETS =================
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open(SHEET_NAME).sheet1

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📊 Umumiy hisobot"]]
    await update.message.reply_text(
        "Kerakli bo‘limni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ================= MENU =================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 Umumiy hisobot":
        keyboard = [["📄 Shu yerda", "📊 Excel"]]
        await update.message.reply_text(
            "Qanday ko‘rmoqchisiz?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "📄 Shu yerda":
        await send_text_report(update)

    elif text == "📊 Excel":
        await send_excel(update)

# ================= TEXT HISOBOT =================
async def send_text_report(update: Update):
    data = sheet.get("A2:B10")

    msg = "📊 UMUMIY HISOBOT\n\n"
    for row in data:
        msg += f"{row[0]}: {row[1]}\n"

    await update.message.reply_text(msg)

# ================= EXCEL =================
async def send_excel(update: Update):
    data = sheet.get_all_values()
    df = pd.DataFrame(data)

    file_path = "hisobot.xlsx"
    df.to_excel(file_path, index=False)

    await update.message.reply_document(document=open(file_path, "rb"))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, menu))

    print("Bot ishlayapti...")
    app.run_polling()

if __name__ == "__main__":
    main()
