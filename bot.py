import time
import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8523653919:AAGQarXbIP203rcyE8EmCKTAL_FksbJikr8"

# =========================
# COINS (RESTORED + BIG LIST)
# =========================
COINS = [
    "BTCUSDT","ETHUSDT","SOLUSDT","TONUSDT","XRPUSDT",
    "ADAUSDT","DOGEUSDT","BNBUSDT","AVAXUSDT","MATICUSDT",
    "DOTUSDT","LTCUSDT","TRXUSDT","SHIBUSDT","ATOMUSDT",
    "NEARUSDT","APTUSDT","OPUSDT","ARBUSDT","FILUSDT",
    "ICPUSDT","INJUSDT","SUIUSDT","SEIUSDT","AAVEUSDT",
    "RUNEUSDT","FLOWUSDT","GALAUSDT","FETUSDT","PEPEUSDT",
    "XLMUSDT","FTMUSDT","RNDRUSDT","IMXUSDT","THETAUSDT",
    "KASUSDT","BONKUSDT","TIAUSDT","WLDUSDT","ORDIUSDT"
]

CACHE = {}
CACHE_TIME = 0
CACHE_TTL = 5

session: aiohttp.ClientSession | None = None


# =========================
# FETCH SAFE (NO CRASH)
# =========================
async def fetch_prices():
    global session

    url = "https://api.binance.com/api/v3/ticker/price"

    try:
        async with session.get(url, timeout=10) as r:
            data = await r.json()

        result = {}
        for item in data:
            if item["symbol"] in COINS:
                result[item["symbol"]] = float(item["price"])

        return result

    except:
        return CACHE


async def get_prices():
    global CACHE, CACHE_TIME

    now = time.time()

    if CACHE and now - CACHE_TIME < CACHE_TTL:
        return CACHE

    new = await fetch_prices()

    if new:
        CACHE = new
        CACHE_TIME = now

    return CACHE


# =========================
# MENU UI (RESTORED)
# =========================
def menu():
    buttons = []
    row = []

    for i, c in enumerate(COINS[:30]):
        row.append(InlineKeyboardButton(c.replace("USDT",""), callback_data=c))
        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("💱 CONVERT", callback_data="CONVERT"),
        InlineKeyboardButton("📊 TOP", callback_data="TOP"),
        InlineKeyboardButton("🔔 ALERTS", callback_data="ALERTS"),
    ])

    buttons.append([
        InlineKeyboardButton("🔄 REFRESH", callback_data="REFRESH")
    ])

    return InlineKeyboardMarkup(buttons)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 CRYPTO BOT STABLE (RAILWAY READY)",
        reply_markup=menu()
    )


# =========================
# CALLBACK HANDLER
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data
    prices = await get_prices()

    # ================= CONVERT SCREEN =================
    if data == "CONVERT":
        await q.edit_message_text(
            "💱 CONVERTER MODE\n\nПиши:\nBTC 0.5\nETH 1\nSOL 2",
            reply_markup=menu()
        )
        return

    # ================= TOP =================
    if data == "TOP":
        text = "📊 TOP COINS\n\n"
        for k in list(prices.keys())[:10]:
            text += f"{k[:-4]}: ${prices[k]}\n"

        await q.edit_message_text(text, reply_markup=menu())
        return

    # ================= ALERTS (SAFE) =================
    if data == "ALERTS":
        await q.edit_message_text(
            "🔔 ALERTS MODE\n(coming soon safe version)",
            reply_markup=menu()
        )
        return

    # ================= REFRESH =================
    if data == "REFRESH":
        global CACHE_TIME
        CACHE_TIME = 0
        await q.edit_message_text("🔄 Updated", reply_markup=menu())
        return

    # ================= COIN =================
    price = prices.get(data)

    if not price:
        await q.edit_message_text(
            "⚠️ No data (retry)",
            reply_markup=menu()
        )
        return

    await q.edit_message_text(
        f"💰 {data.replace('USDT','')}: ${price}",
        reply_markup=menu()
    )


# =========================
# TEXT CONVERTER (FIXED)
# =========================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = await get_prices()

    try:
        text = update.message.text.upper().split()

        if len(text) != 2:
            return

        coin = text[0] + "USDT"
        amount = float(text[1])

        price = prices.get(coin)

        if not price:
            await update.message.reply_text("❌ Unknown coin")
            return

        result = price * amount

        await update.message.reply_text(
            f"💱 {amount} {text[0]} = ${result:.4f} USDT"
        )

    except:
        await update.message.reply_text("❌ Format: BTC 0.5")


# =========================
# INIT SESSION (IMPORTANT FIX)
# =========================
async def post_init(app: Application):
    global session
    session = aiohttp.ClientSession()


async def post_shutdown(app: Application):
    global session
    if session:
        await session.close()


# =========================
# MAIN (RAILWAY SAFE)
# =========================
def main():
    app = Application.builder().token(TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    # FIXED CONVERTER (NO CommandHandler(None))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🚀 BOT RUNNING SAFE MODE")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
