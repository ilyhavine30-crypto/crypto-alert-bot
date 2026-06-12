from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os

TOKEN = os.getenv("BOT_TOKEN")

def get_price(coin):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin,
        "vs_currencies": "usd"
    }
    data = requests.get(url, params=params).json()
    return data[coin]["usd"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🚀 Crypto Alert Bot

Команды:

/btc - курс Bitcoin
/eth - курс Ethereum
"""
    await update.message.reply_text(text)

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_price("bitcoin")
    await update.message.reply_text(f"₿ Bitcoin: ${price}")

async def eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_price("ethereum")
    await update.message.reply_text(f"Ξ Ethereum: ${price}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("eth", eth))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
