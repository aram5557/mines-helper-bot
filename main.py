print("=== Я запустился из bot.py ===")
import os
import json
import statistics
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DATA_FILE = "data.json"

# --- Работа с историей
def load_data():
    return json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_user_data(user_id):
    return load_data().get(str(user_id), [])

def save_multiplier(user_id, value):
    data = load_data()
    uid = str(user_id)
    data.setdefault(uid, []).append(value)
    save_data(data)

def clear_user_data(user_id):
    data = load_data()
    data[str(user_id)] = []
    save_data(data)

# --- Логика предсказания
def analyze_trend(values):
    last5 = values[-5:] if len(values) >= 5 else values
    lows = sum(1 for v in last5 if v < 1.5)
    highs = sum(1 for v in last5 if v >= 2)
    if lows >= 4:
        return "📉 Много низких значений.\n🔮 Возможен x2–x5"
    elif highs >= 4:
        return "📈 Были высокие множители.\n🔮 Возможен x1.05–x1.5"
    return "🤔 Тренд неясен.\n🔮 Возможен x1.5–x3.0"

# --- Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📥 Добавить /add", "📊 Статистика /stats"],
        ["🔮 Прогноз /predict", "🧹 Очистить /clear"],
        ["ℹ️ Помощь /help"]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Я LuckyJet аналитик. Выбирай команду снизу ⬇️", reply_markup=markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Команды:\n"
        "/add 1.25 2.5 — добавить множители\n"
        "/round 1.8 — добавить + предсказание\n"
        "/predict — предсказать следующий\n"
        "/stats — показать статистику\n"
        "/clear — очистить историю\n"
        "/help — помощь\n"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    values = []
    for val in context.args:
        try:
            num = float(val)
            save_multiplier(user_id, num)
            values.append(num)
        except:
            continue
    if values:
        await update.message.reply_text(f"✅ Добавлены: {', '.join(map(str, values))}")
    else:
        await update.message.reply_text("⚠️ Используй: /add 1.5 2.33")

async def round_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        return await update.message.reply_text("⚠️ Пример: /round 2.33")
    try:
        val = float(context.args[0])
        save_multiplier(user_id, val)
        prediction = analyze_trend(get_user_data(user_id))
        await update.message.reply_text(f"➕ Добавлен: {val}\n{prediction}")
    except:
        await update.message.reply_text("❌ Неверный формат.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    values = get_user_data(user_id)
    if not values:
        return await update.message.reply_text("⚠️ Сначала добавь историю через /add.")
    trend = analyze_trend(values)
    await update.message.reply_text(f"🔮 Прогноз:\n{trend}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    values = get_user_data(user_id)
    if not values:
        return await update.message.reply_text("⚠️ У тебя ещё нет данных.")
    msg = (
        f"📊 Всего: {len(values)} значений\n"
        f"Среднее: {round(statistics.mean(values), 2)}\n"
        f"Медиана: {round(statistics.median(values), 2)}\n"
        f"Мин: {min(values)} | Макс: {max(values)}\n"
        f"Последний x>2.0: {next((v for v in reversed(values) if v > 2.0), '—')}"
    )
    await update.message.reply_text(msg)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_user_data(update.effective_user.id)
    await update.message.reply_text("🧹 История очищена!")

# --- Запуск
async def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise Exception("❌ Переменная TELEGRAM_BOT_TOKEN не установлена")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("round", round_cmd))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("clear", clear))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
