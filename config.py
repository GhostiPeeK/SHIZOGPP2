import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
WEBSITE_URL = os.getenv('WEBSITE_URL', 'https://shizogp.com')
VIP_CHAT_LINK = os.getenv('VIP_CHAT_LINK', 'https://t.me/+r3rxYlBjbTYyMDY6')
VIP_PRICE_COINS = int(os.getenv('VIP_PRICE_COINS', 550))
VIP_DURATION_DAYS = int(os.getenv('VIP_DURATION_DAYS', 30))

# Получаем username бота (нужно будет установить после запуска)
BOT_USERNAME = None

async def set_bot_username(bot):
    global BOT_USERNAME
    me = await bot.get_me()
    BOT_USERNAME = me.username