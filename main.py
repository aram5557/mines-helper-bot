import os
import json
import statistics
import logging
from telegram import Update, InputFile, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract
import pandas as pd

DATA_FILE = "data.json"

# --- Утилиты сохранения ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_user_data(user_id):
    data = load_data()
    return data.get(str(user_id), [])

def save_multiplier(user_id, value):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid].append(value)
    save_data(data)

def clear_user_data(user_id):
    data = load_data()
    data[str(user_id)] = []
    save_data(data)

def analyze_trend(values):
    recent = values[-5:] if len(values) >= 5 else values
    low = sum(1 for v in recent if v < 1.5)
    high = sum(1 for v in recent if v > 2.0)
    if low >= 4:
        return "📉 Последние раунды были низкими.\n🔮 Прогноз: 2.00–4.50x"
    elif high >= 4:
        return "📈 Были высокие множители.\n🔮 Прогноз: 1.05–1.50x"
    else:
        return "🤔 Тренд неясен.\n🔮 Прогноз: 1.50–2.50x"

# --- Обработчики команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📥 Добавить множитель", "📊 Статистика"],
        ["🔮 Прогноз", "📈 График"],
        ["📄 Отчёт", "📚 Помощь"],
        ["🧹 Очистить историю"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Я анализатор LuckyJet. Выбирай действие ниже:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Доступные команды:\n\n"
        "/start — показать меню\n"
        "/help — список всех команд\n"
        "/add 1.23 2.45 — добавить множители\n"
        "/round 1.11 — добавить и получить прогноз\n"
        "/predict — предсказать следующий множитель\n"
        "/stats — статистика\n"
        "/plot — график истории\n"
        "/report — Excel-отчёт\n"
        "/clear — очистить свою историю\n\n"
        "📷 Можно также отправить скрин с множителями — бот сам распознает!"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    clear_user_data(user_id)
    await update.message.reply_text("🧹 История очищена!")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    values = []
    for val in context.args:
        try:
            f = float(val)
            values.append(f)
            save_multiplier(user_id, f)
        except:
            pass
    if values:
        await update.message.reply_text(f"✅ Добавлены: {', '.join(map(str, values))}")
    else:
        await update.message.reply_text("⚠️ Используй: /add 1.23 2.34")

async def round_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text("⚠️ Укажи множитель: /round 1.25")
        return
    try:
        value = float(context.args[0])
        save_multiplier(user_id, value)
        trend = analyze_trend(get_user_data(user_id))
        await update.message.reply_text(f"➕ Добавлен: {value}\n{trend}")
    except:
        await update.message.reply_text("⚠️ Неверный множитель.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    values = get_user_data(user_id)
    if not values:
        await update.message.reply_text("⚠️ У тебя нет данных. Добавь через /add.")
        return
    recent = values[-5:]
    trend = analyze_trend(values)
    await update.message.reply_text(f"📊 Последние: {', '.join(map(str, recent))}\n{trend}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    values = get_user_data(user_id)
    if not values:
        await update.message.reply_text("⚠️ Нет данных.")
        return
    msg = (
        f"📈 Статистика:\n"
        f"- Всего: {len(values)}\n"
        f"- Среднее: {round(statistics.mean(values), 2)}\n"
        f"- Медиана: {round(statistics.median(values), 2)}\n"
        f"- Мин: {min(values)}\n"
        f"- Макс: {max(values)}\n"
        f"- Последний x > 2.0: {next((v for v in reversed(values) if v > 2.0), '—')}"
    )
    await update.message.reply_text(msg)

async def plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    values = get_user_data(user_id)
    if not values:
        await update.message.reply_text("⚠️ Нет данных.")
        return
    plt.figure()
    plt.plot(values, marker='o')
    plt.title("История множителей")
    plt.xlabel("Раунд")
    plt.ylabel("Множитель")
    plt.grid(True)
    plt.savefig("plot.png")
    plt.close()
    await update.message.reply_photo(photo=InputFile("plot.png"))

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    values = get_user_data(user_id)
    if not values:
        await update.message.reply_text("⚠️ Нет данных.")
        return
    df = pd.DataFrame(values, columns=["Multiplier"])
    filename = f"report_{user_id}.xlsx"
    df.to_excel(filename, index=False)
    await update.message.reply_document(document=InputFile(filename))

async def ocr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()
    await file.download_to_drive("ocr.jpg")
    image = Image.open("ocr.jpg")
    text = pytesseract.image_to_string(image)
    numbers = [float(x) for x in text.replace(",", ".").split() if x.replace(".", "", 1).isdigit()]
    if not numbers:
        await update.message.reply_text("⚠️ Не удалось распознать множители.")
        return
    for n in numbers:
        save_multiplier(user_id, n)
    trend = analyze_trend(get_user_data(user_id))
    await update.message.reply_text(f"📸 Распознано: {', '.join(map(str, numbers))}\n{trend}")

# --- Основной запуск ---
async def main():
    import asyncio
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ Переменная TELEGRAM_BOT_TOKEN не установлена!")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("round", round_command))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("plot", plot))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.PHOTO, ocr_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📚 Помощь"), help_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📊 Статистика"), stats))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🔮 Прогноз"), predict))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📈 График"), plot))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📄 Отчёт"), report))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🧹 Очистить историю"), clear))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
