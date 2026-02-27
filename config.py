import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Берется из окружения BotHost

if not BOT_TOKEN:
    raise ValueError("❌ НЕТ ТОКЕНА! Добавьте BOT_TOKEN в переменные окружения")

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# ========== ПРОСТЕЙШИЕ КОМАНДЫ ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"🔥 Бот SHIZOGP работает!\n"
        f"🆔 Твой ID: {message.from_user.id}"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 Доступные команды:\n"
        "/start - Начать\n"
        "/help - Помощь\n"
        "/info - Информация"
    )

@dp.message(Command("info"))
async def cmd_info(message: Message):
    await message.answer(
        f"🤖 Информация о боте:\n"
        f"Имя: SHIZOGP\n"
        f"Версия: 1.0\n"
        f"Сервер: BotHost"
    )

@dp.message()
async def echo_message(message: Message):
    """Отвечает на любое сообщение"""
    await message.answer(f"Ты написал: {message.text}")

# ========== ЗАПУСК ==========
async def main():
    print("🔥 SHIZOGP БОТ ЗАПУЩЕН!")
    print(f"🤖 Бот: @{(await bot.get_me()).username}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

