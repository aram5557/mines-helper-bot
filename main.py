import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

GRID_SIZE = 5
MINES_COUNT = 3
CELLS_TO_REVEAL = (6, 8)

def generate_cells():
    letters = ['A', 'B', 'C', 'D', 'E']
    numbers = ['1', '2', '3', '4', '5']
    return [f"{l}{n}" for l in letters for n in numbers]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для подсказок в 'Мины' на 1Win. Напиши /mines, чтобы получить 6–8 клеток!"
    )

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
