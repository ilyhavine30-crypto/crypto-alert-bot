import os
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ======================
# TOKEN (из env)
# ======================
TOKEN = "8523653919:AAEh_dNfYhKTzV2v3BIgmVm74GUQcsCd8lg"
# ======================
# COINS
# ======================
COINS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "TON": "the-open-network",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "BNB": "binancecoin",
    "AVAX": "avalanche-2",
    "MATIC": "polygon"
}

alerts = {}

# кеш чтобы не спамить API
price_cache = {}


# ======================
# PRICE (СТАБИЛЬНЫЙ)
# ======================
def get_price(coin_id: str):
    try:
        if coin_id in price_cache:
            return price_cache[coin_id]

        url = "https://api.coingecko.com/api/v3/simple/price"

        r = requests.get(
            url,
            params={"ids": coin_id, "vs_currencies": "usd"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        data = r.json()

        if coin_id not in data:
            return None

        price = data[coin_id]["usd"]
        price_cache[coin_id] = price

        return price

    except:
        return None


# ======================
# KEYBOARD
# ======================
def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("BTC", callback_data="BTC"),
            InlineKeyboardButton("ETH", callback_data="ETH"),
            InlineKeyboardButton("SOL", callback_data="SOL")
        ],
        [
            InlineKeyboardButton("TON", callback_data="TON"),
            InlineKeyboardButton("XRP", callback_data="XRP"),
            InlineKeyboardButton("ADA", callback_data="ADA")
        ],
        [
            InlineKeyboardButton("DOGE", callback_data="DOGE"),
            InlineKeyboardButton("BNB", callback_data="BNB"),
            InlineKeyboardButton("AVAX", callback_data="AVAX")
        ],
        [
            InlineKeyboardButton("📊 TOP", callback_data="TOP"),
            InlineKeyboardButton("🔔 ALERTS", callback_data="ALERTS")
        ]
    ])


# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Crypto Bot STABLE MODE\n\n"
        "Выбери монету или команду:",
        reply_markup=main_keyboard()
    )


# ======================
# PRICE
# ======================
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Пример: /price BTC")

    symbol = context.args[0].upper()

    if symbol not in COINS:
        return await update.message.reply_text("❌ Неизвестная монета")

    price = get_price(COINS[symbol])

    if not price:
        return await update.message.reply_text("❌ Нет данных")

    await update.message.reply_text(f"💰 {symbol}: ${price}")


# ======================
# ALERT
# ======================
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("Пример: /alert BTC 60000")

    symbol = context.args[0].upper()
    target = float(context.args[1])

    if symbol not in COINS:
        return await update.message.reply_text("❌ Неизвестная монета")

    user_id = update.effective_user.id
    alerts.setdefault(user_id, []).append((symbol, target))

    await update.message.reply_text(f"🔔 Алерт: {symbol} → ${target}")


# ======================
# ALERTS LIST
# ======================
async def show_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_alerts = alerts.get(user_id, [])

    if not user_alerts:
        return await update.message.reply_text("Нет алертов")

    text = "🔔 Твои алерты:\n"
    for s, t in user_alerts:
        text += f"{s} → ${t}\n"

    await update.message.reply_text(text)


# ======================
# TOP
# ======================
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"

        r = requests.get(url, params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 5,
            "page": 1
        }, timeout=10)

        data = r.json()

        text = "📊 TOP COINS:\n\n"

        for c in data:
            text += f"{c['symbol'].upper()} - ${c['current_price']}\n"

        await update.message.reply_text(text)

    except:
        await update.message.reply_text("❌ TOP недоступен")


# ======================
# BUTTONS (ГЛАВНОЕ ИСПРАВЛЕНИЕ)
# ======================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data

    # MONETES
    if data in COINS:
        price = get_price(COINS[data])

        if not price:
            return await q.edit_message_text("❌ Нет данных")

        return await q.edit_message_text(f"💰 {data}: ${price}")

    # TOP
    if data == "TOP":
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"

            r = requests.get(url, params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 5,
                "page": 1
            }, timeout=10)

            data = r.json()

            text = "📊 TOP COINS:\n\n"
            for c in data:
                text += f"{c['symbol'].upper()} - ${c['current_price']}\n"

            return await q.edit_message_text(text)

        except:
            return await q.edit_message_text("❌ TOP error")

    # ALERTS
    if data == "ALERTS":
        user_id = update.effective_user.id
        user_alerts = alerts.get(user_id, [])

        if not user_alerts:
            return await q.edit_message_text("Нет алертов")

        text = "🔔 ALERTS:\n\n"
        for s, t in user_alerts:
            text += f"{s} → ${t}\n"

        return await q.edit_message_text(text)


# ======================
# ALERT LOOP (БЕЗ job_queue)
# ======================
async def alert_loop(app: Application):
    while True:
        for user_id, user_alerts in list(alerts.items()):
            for item in user_alerts[:]:
                symbol, target = item
                price = get_price(COINS[symbol])

                if price and price >= target:
                    try:
                        await app.bot.send_message(
                            chat_id=user_id,
                            text=f"🚨 {symbol} достиг ${target}\nСейчас: ${price}"
                        )
                        user_alerts.remove(item)
                    except:
                        pass

        await asyncio.sleep(30)


# ======================
# START BACKGROUND TASK
# ======================
async def post_init(app: Application):
    asyncio.create_task(alert_loop(app))


# ======================
# MAIN
# ======================
def main():
    if not TOKEN:
        print("❌ BOT_TOKEN не задан")
        return

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("alerts", show_alerts))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CallbackQueryHandler(button))

    print("🚀 Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()

