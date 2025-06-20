import os
import json
import statistics
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
import pytesseract

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

DATA_FILE = "data.json"

# Загрузка и сохранение данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

user_data = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь историю множителей через /add, например:\n/add 1.05 2.33 27.2\n"
        "Также можно отправить скриншот с множителями для распознавания."
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
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
    save_data(user_data)
    await update.message.reply_text(f"Добавлено {len(multipliers)} множителей. Всего теперь: {len(user_data[user_id])}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = user_data.get(user_id)

    if not data:
        await update.message.reply_text("Нет данных. Добавь множители через /add")
        return

    avg = statistics.mean(data)
    median = statistics.median(data)
    maximum = max(data)
    minimum = min(data)
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
    user_id = str(update.effective_user.id)
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

async def send_plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = user_data.get(user_id)

    if not data:
        await update.message.reply_text("Нет данных для построения графика.")
        return

    plt.figure(figsize=(6,4))
    plt.plot(data, marker='o')
    plt.title("Множители по раундам")
    plt.xlabel("Раунд")
    plt.ylabel("Множитель")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("plot.png")
    plt.close()

    with open("plot.png", "rb") as f:
        await update.message.reply_photo(f)

def create_excel_report(user_id, data):
    df = pd.DataFrame({"Раунд": list(range(1, len(data)+1)), "Множитель": data})
    filename = f"report_{user_id}.xlsx"
    df.to_excel(filename, index=False)
    return filename

async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = user_data.get(user_id)
    if not data:
        await update.message.reply_text("Нет данных для отчёта.")
        return

    filename = create_excel_report(user_id, data)
    with open(filename, "rb") as f:
        await update.message.reply_document(f)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    photo_file = await update.message.photo[-1].get_file()
    filename = f"screenshot_{user_id}.png"
    await photo_file.download_to_drive(filename)

    # Распознаём текст
    text = pytesseract.image_to_string(Image.open(filename))

    # Простая попытка извлечь множители из текста (через разделение по пробелам и фильтр float)
    import re
    matches = re.findall(r"\d+\.\d+|\d+", text)
    multipliers = []
    for m in matches:
        try:
            val = float(m)
            multipliers.append(val)
        except:
            pass

    if not multipliers:
        await update.message.reply_text("Не удалось распознать множители на скриншоте.")
        return

    if user_id not in user_data:
        user_data[user_id] = []

    user_data[user_id].extend(multipliers)
    save_data(user_data)
    await update.message.reply_text(f"Распознано и добавлено {len(multipliers)} множителей из скриншота.")

if __name__ == "__main__":
    import logging
    import sys

    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("plot", send_plot))
    app.add_handler(CommandHandler("report", send_report))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Бот запущен...")
    app.run_polling()
import asyncio
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running")

app_http = web.Application()
app_http.add_routes([web.get('/', handle)])

async def run_webserver():
    runner = web.AppRunner(app_http)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8000)))
    await site.start()
    print("HTTP server started")

async def main():
    # Запускаем вебсервер параллельно с ботом
    await run_webserver()
    # Запускаем бота (app.run_polling() — в синхронном режиме, можно обернуть или перенести в asyncio)
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
