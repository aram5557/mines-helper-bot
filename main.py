from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import statistics

# Хранилище данных по user_id (для простоты, в оперативке)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь историю множителей через /add, например:\n/add 1.05 2.33 27.2"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not args:
        await update.message.reply_text("Пожалуйста, укажи множители после команды /add")
        return

    try:
        multipliers = [float(x) for x in args]
    except ValueError:
        await update.message.reply_text("Ошибка: множители должны быть числами, например: 1.05 2.33 27.2")
        return

    if user_id not in user_data:
        user_data[user_id] = []

    user_data[user_id].extend(multipliers)
    await update.message.reply_text(f"Добавлено {len(multipliers)} множителей. Всего теперь: {len(user_data[user_id])}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data.get(user_id)

    if not data:
        await update.message.reply_text("Нет данных. Добавь множители через /add")
        return

    avg = statistics.mean(data)
    median = statistics.median(data)
    maximum = max(data)
    minimum = min(data)
    # Последний большой множитель (больше 5.0)
    big_threshold = 5.0
    last_big = None
    for val in reversed(data):
        if val > big_threshold:
            last_big = val
            break

    reply = (
        f"Статистика:\n"
        f"Среднее: {avg:.2f}\n"
        f"Медиана: {median:.2f}\n"
        f"Максимум: {maximum}\n"
        f"Минимум: {minimum}\n"
        f"Последний большой множитель (> {big_threshold}): {last_big if last_big else 'не найден'}"
    )
    await update.message.reply_text(reply)

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data.get(user_id)

    if not data or len(data) < 5:
        await update.message.reply_text("Недостаточно данных для предсказания. Добавь хотя бы 5 множителей через /add")
        return

    last_5 = data[-5:]
    low_threshold = 2.0
    if all(x < low_threshold for x in last_5):
        approx = statistics.mean(last_5) * 1.5
        await update.message.reply_text(
            f"Последние 5 раундов были низкими. Высокий множитель может быть скоро.\n"
            f"Примерный множитель: {approx:.2f}"
        )
    else:
        await update.message.reply_text("Сейчас нет явных признаков высокого множителя.")

if __name__ == "__main__":
    import os

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("predict", predict))

    print("Бот запущен...")
    app.run_polling()

async def mines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_cells = generate_cells()
    suggested = random.sample(all_cells, random.randint(*CELLS_TO_REVEAL))
    await update.message.reply_text(
        "🟩 Предположительно безопасные клетки:\n\n" + ", ".join(suggested)
    )

def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mines", mines))
    
    print("✅ Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()
