import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8523653919:AAGQarXbIP203rcyE8EmCKTAL_FksbJikr8"

# =========================
# FULL COIN TABLE (RESTORED + EXPANDED)
# =========================
COINS = [
    "BTCUSDT","ETHUSDT","SOLUSDT","TONUSDT","XRPUSDT",
    "ADAUSDT","DOGEUSDT","BNBUSDT","AVAXUSDT","MATICUSDT",
    "DOTUSDT","LTCUSDT","TRXUSDT","SHIBUSDT","ATOMUSDT",
    "NEARUSDT","APTUSDT","OPUSDT","ARBUSDT","FILUSDT",
    "ICPUSDT","INJUSDT","SUIUSDT","SEIUSDT","AAVEUSDT",
    "RUNEUSDT","FLOWUSDT","GALAUSDT","FETUSDT","PEPEUSDT",
    "XLMUSDT","FTMUSDT","RNDRUSDT","IMXUSDT","THETAUSDT",
    "KASUSDT","BONKUSDT","TIAUSDT","WLDUSDT","ORDIUSDT",
    "JUPUSDT","PYTHUSDT","DYDXUSDT","MINAUSDT","1INCHUSDT"
]

# =========================
# CACHE (STABILITY FIX)
# =========================
cache = {}
last_update = 0
CACHE_TTL = 5

# =========================
# CONVERTER STATE (DO NOT TOUCH LOGIC)
# =========================
user_mode = {}


# =========================
# PRICE FETCH (SAFE)
# =========================
def get_prices():
    global cache, last_update

    if cache and time.time() - last_update < CACHE_TTL:
        return cache

    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        data = requests.get(url, timeout=10).json()

        result = {}
        for i in data:
            if i["symbol"] in COINS:
                result[i["symbol"]] = float(i["price"])

        cache = result
        last_update = time.time()

        return result

    except:
        return cache


# =========================
# MENU (FIXED GRID 3x3)
# =========================
def menu():
    buttons = []
    row = []

    for c in COINS:
        row.append(InlineKeyboardButton(c.replace("USDT", ""), callback_data=c))

        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("💱 CONVERT", callback_data="CONVERT"),
        InlineKeyboardButton("📊 TOP", callback_data="TOP"),
        InlineKeyboardButton("🔄 REFRESH", callback_data="REFRESH")
    ])

    return InlineKeyboardMarkup(buttons)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 CRYPTO PRO BOT\nChoose coin or convert:",
        reply_markup=menu()
    )


# =========================
# BUTTON HANDLER
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data
    prices = get_prices()

    # ================= CONVERT MODE (UNCHANGED) =================
    if data == "CONVERT":
        user_mode[q.from_user.id] = "convert"

        await q.edit_message_text(
            "💱 CONVERTER MODE\n\n"
            "Send format:\n"
            "BTC 1.5\nETH 0.2\nSOL 3",
            reply_markup=menu()
        )
        return

    # ================= TOP =================
    if data == "TOP":
        top = sorted(prices.items(), key=lambda x: x[1], reverse=True)[:10]

        text = "📊 TOP 10:\n\n"
        for s, p in top:
            text += f"{s.replace('USDT','')}: ${p}\n"

        await q.edit_message_text(text, reply_markup=menu())
        return

    # ================= REFRESH =================
    if data == "REFRESH":
        get_prices()
        await q.edit_message_text("🔄 Updated", reply_markup=menu())
        return

    # ================= COIN PRICE =================
    price = prices.get(data)

    if not price:
        await q.edit_message_text("❌ No data", reply_markup=menu())
        return

    await q.edit_message_text(
        f"💰 {data.replace('USDT','')}: ${price}",
        reply_markup=menu()
    )


# =========================
# TEXT HANDLER (CONVERTER - NOT CHANGED)
# =========================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_mode.get(user_id) != "convert":
        return

    try:
        text = update.message.text.upper().split()
        coin = text[0]
        amount = float(text[1])

        prices = get_prices()

        symbol = coin + "USDT"
        price = prices.get(symbol)

        if not price:
            return await update.message.reply_text("❌ Unknown coin")

        result = amount * price

        await update.message.reply_text(
            f"💱 RESULT\n\n{amount} {coin} = {result:.2f} USDT"
        )

    except:
        await update.message.reply_text("❌ Format: BTC 1.5")


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🚀 STABLE PRO BOT RUNNING")
    app.run_polling()


if __name__ == "__main__":
    main()

