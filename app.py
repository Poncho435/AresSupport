import os
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ===== ТОКЕН =====
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # Берем из переменных окружения!
ADMIN_ID = 5461117804
# =================

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Ваша логика бота (копируете сюда) ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Бот работает!")

# Остальные ваши хендлеры...
# -----------------------------------------

# --- Flask эндпоинты для Render ---
@app.route("/")
def home():
    return "Bot is running!"

@app.route("/health")
def health():
    return "OK", 200

# --- Запуск бота в отдельном потоке ---
def run_bot():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask (слушает порт $PORT)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
