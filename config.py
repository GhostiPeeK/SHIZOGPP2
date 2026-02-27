#!/usr/bin/env python3
"""
SHIZOGP - Telegram Bot for CS2 Skins Trading
Главный файл запуска бота
"""

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


from bot.handlers import router
from bot.database import init_db
from bot.config import BOT_TOKEN, set_bot_username




# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка токена
if not BOT_TOKEN:
    logger.error("❌ Нет токена! Добавь BOT_TOKEN в .env файл")
    exit(1)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

async def on_startup():
    """Действия при запуске"""
    logger.info("🚀 Запуск бота SHIZOGP...")
    
    # Инициализация базы данных
    await init_db()
    logger.info("✅ База данных готова")
    
    # Получаем информацию о боте
    await set_bot_username(bot)
    logger.info(f"✅ Бот: @{bot._me.username}")

async def on_shutdown():
    """Действия при остановке"""
    logger.info("👋 Бот остановлен")

async def main():
    """Главная функция"""
    await on_startup()
    
    try:
        logger.info("🔥 Бот запущен и готов к работе!")
        await dp.start_polling(bot)
    finally:
        await on_shutdown()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

