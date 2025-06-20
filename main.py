import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import statistics

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Сохраняем историю множителей
multipliers = []

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['/predict'], ['/stats'], ['/help']]
    await update.message.reply_text(
        "👋 Привет! Я анализатор LuckyJet. Введи множители через запятую, например:\n1.23, 2.34, 3.01",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# Команда /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
📋 Доступные команды:
/start — запуск бота и меню
/stats — показать статистику по текущим множителям
/predict — предсказать следующий раунд на основе истории
/help — список команд
""")

# Команда /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not multipliers:
        await update.message.reply_text("Нет данных. Введите множители.")
        return
    avg = round(statistics.mean(multipliers), 2)
    med = round(statistics.median(multipliers), 2)
    maxx = max(multipliers)
    minn = min(multipliers)
    last_big = next((x for x in reversed(multipliers) if x > 5), "не найден")
    await update.message.reply_text(
        f"📊 Статистика:\n"
        f"Среднее: {avg}\n"
        f"Медиана: {med}\n"
        f"Макс: {maxx}\n"
        f"Мин: {minn}\n"
        f"Последний x5+: {last_big}"
    )

# Команда /predict
async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not multipliers or len(multipliers) < 5:
        await update.message.reply_text("Недостаточно данных для прогноза.")
        return
    recent = multipliers[-5:]
    low = all(x < 2 for x in recent)
    if low:
        await update.message.reply_text("Последние 5 раундов были низкими. Возможно, скоро x5+!")
    else:
        await update.message.reply_text("Скорее всего, следующий множитель будет средним.")
    forecast = round(statistics.mean(recent) * 1.3, 2)
    await update.message.reply_text(f"📈 Прогнозный множитель: ~ {forecast}x")

# Обработка сообщений с множителями
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        values = [float(x.strip()) for x in text.split(",")]
        multipliers.extend(values)
        await update.message.reply_text(f"✅ Добавлено: {values}")
    except:
        await update.message.reply_text("Ошибка: введите множители через запятую, например: 1.2, 2.3")

# Запуск бота
async def main():
    from os import getenv
    TOKEN = getenv("BOT_TOKEN")  # Убедись, что переменная окружения задана
    if not TOKEN:
        print("❌ Переменная окружения BOT_TOKEN не задана!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
