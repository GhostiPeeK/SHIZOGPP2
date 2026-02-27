from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json

from .database import *
from .keyboards import *
from .utils import *

router = Router()

# ========== СОСТОЯНИЯ ==========
class SellStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_quality = State()
    waiting_for_price = State()
    waiting_for_link = State()

class ReviewStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_comment = State()

# ========== КОМАНДА СТАРТ ==========
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name
    
    # Парсим реферальный код
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            if referrer_id == user_id:
                referrer_id = None
        except:
            pass
    
    # Создаём или обновляем пользователя
    await create_user(user_id, username, full_name, referrer_id)
    
    user = await get_user(user_id)
    
    # Стартовое сообщение
    welcome_text = (
        f"👋 Добро пожаловать в **SHIZOGP**!\n\n"
        f"🆔 Твой ID: `{user_id}`\n"
        f"💰 Баланс: **{user['balance_coins']}** монет\n"
        f"⭐ Рейтинг: **{user['rating']:.1f}** ({user['rating_count']} отзывов)\n\n"
        f"🎮 Здесь ты можешь покупать и продавать скины CS2\n"
        f"👑 VIP статус даёт доступ к закрытому чату"
    )
    
    from .config import WEBSITE_URL, VIP_CHAT_LINK
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(WEBSITE_URL, VIP_CHAT_LINK),
        parse_mode="Markdown"
    )

# ========== БАЛАНС ==========
@router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    text = (
        f"💰 **ТВОЙ БАЛАНС**\n\n"
        f"🪙 Монеты: **{user['balance_coins']}**\n"
        f"₿ Крипта: **{user['balance_crypto']:.6f}** BTC\n\n"
        f"📊 Статистика:\n"
        f"• Продаж: **{user['total_sales']}**\n"
        f"• Покупок: **{user['total_purchases']}**\n"
        f"• Рейтинг: **{user['rating']:.1f}** ⭐\n\n"
    )
    
    if user['vip_status']:
        text += f"👑 VIP до **{user['vip_until'][:10]}**"
    else:
        text += f"👑 VIP стоит 550 монет (30 дней)"
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")

# ========== РЕФЕРАЛЫ ==========
@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery):
    user_id = callback.from_user.id
    from .config import BOT_USERNAME
    
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        count = await cursor.fetchone()
        referrals = count[0] if count else 0
    
    text = (
        f"🤝 **РЕФЕРАЛЬНАЯ ПРОГРАММА**\n\n"
        f"👥 Твои рефералы: **{referrals}**\n"
        f"💰 Бонус за друга: **50 монет**\n\n"
        f"🔗 Твоя ссылка:\n`{ref_link}`\n\n"
        f"📤 Отправь её друзьям и получай бонусы!"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")

# ========== ПРОДАЖА СКИНА ==========
@router.callback_query(F.data == "sell")
async def sell_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SellStates.waiting_for_name)
    await callback.message.edit_text(
        "💸 **ПРОДАЖА СКИНА**\n\n"
        "Шаг 1/4: Введи название скина\n"
        "Пример: `AK-47 | Redline`",
        parse_mode="Markdown"
    )

@router.message(SellStates.waiting_for_name)
async def sell_name(message: Message, state: FSMContext):
    await state.update_data(skin_name=message.text)
    await state.set_state(SellStates.waiting_for_quality)
    await message.answer(
        "📦 Шаг 2/4: Введи качество\n"
        "Пример: `Factory New`, `Minimal Wear`, `Field-Tested`"
    )

@router.message(SellStates.waiting_for_quality)
async def sell_quality(message: Message, state: FSMContext):
    await state.update_data(quality=message.text)
    await state.set_state(SellStates.waiting_for_price)
    await message.answer(
        "💰 Шаг 3/4: Введи цену в USD\n"
        "Только число, например: `1500`"
    )

@router.message(SellStates.waiting_for_price)
async def sell_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError
    except:
        await message.answer("❌ Цена должна быть положительным числом. Попробуй ещё раз:")
        return
    
    await state.update_data(price=price)
    await state.set_state(SellStates.waiting_for_link)
    await message.answer(
        "🔗 Шаг 4/4: Введи ссылку на предмет в Steam\n"
        "Можно просто описание, если нет ссылки"
    )

@router.message(SellStates.waiting_for_link)
async def sell_link(message: Message, state: FSMContext):
    link = message.text.strip()
    data = await state.get_data()
    user_id = message.from_user.id
    
    listing_id = await add_listing(
        user_id,
        data['skin_name'],
        data['quality'],
        data['price'],
        link
    )
    
    await message.answer(
        f"✅ **Объявление #{listing_id} создано!**\n\n"
        f"🎯 Скин: **{data['skin_name']}** ({data['quality']})\n"
        f"💰 Цена: **${data['price']}**\n"
        f"🔗 Ссылка: {link}\n\n"
        f"Когда кто-то купит, ты получишь уведомление."
    )
    await state.clear()

# ========== ПРОСМОТР СКИНОВ ==========
@router.callback_query(F.data == "listings")
async def show_listings(callback: CallbackQuery):
    listings = await get_active_listings(5)
    
    if not listings:
        await callback.message.edit_text(
            "😢 Пока нет активных объявлений.\n"
            "Нажми «Продать скин», чтобы создать первое!",
            reply_markup=get_back_keyboard()
        )
        return
    
    text = "**📋 ДОСТУПНЫЕ СКИНЫ**\n\n"
    for i, item in enumerate(listings, 1):
        text += f"{i}. **{item['skin_name']}** ({item['quality']})\n"
        text += f"   💰 ${item['price_usd']} | 👤 {item['seller_name']} ⭐{item['rating']:.1f}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_listings_keyboard(listings),
        parse_mode="Markdown"
    )

# ========== ДЕТАЛИ СКИНА ==========
@router.callback_query(F.data.startswith("view_"))
async def view_listing(callback: CallbackQuery):
    listing_id = int(callback.data.split("_")[1])
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT l.*, u.username as seller_name, u.rating 
            FROM listings l
            JOIN users u ON l.seller_id = u.user_id
            WHERE l.id = ?
        ''', (listing_id,))
        item = await cursor.fetchone()
    
    if not item:
        await callback.message.edit_text("❌ Скин не найден", reply_markup=get_back_keyboard())
        return
    
    text = (
        f"🎯 **{item['skin_name']}**\n\n"
        f"📦 Качество: **{item['quality']}**\n"
        f"💰 Цена: **${item['price_usd']}**\n"
        f"👤 Продавец: **{item['seller_name']}** ⭐{item['rating']:.1f}\n"
        f"📊 Float: **{item['float_value'] or 'N/A'}**\n"
        f"🎨 Pattern: **{item['pattern'] or 'N/A'}**\n"
        f"👀 Просмотров: **{item['views']}**\n"
        f"🔗 Steam: {item['steam_link']}\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_listing_detail_keyboard(listing_id),
        parse_mode="Markdown"
    )

# ========== ПОКУПКА ==========
@router.callback_query(F.data.startswith("buy_"))
async def buy_listing_handler(callback: CallbackQuery):
    listing_id = int(callback.data.split("_")[1])
    buyer_id = callback.from_user.id
    
    success, message = await buy_listing(listing_id, buyer_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ **{message}**\n\n"
            f"Сделка оформлена! Проверь свои сделки в разделе «Мои сделки».",
            reply_markup=get_back_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"❌ {message}",
            reply_markup=get_back_keyboard()
        )

# ========== АДМИН ПАНЕЛЬ ==========
@router.message(Command("admin"))
async def admin_panel(message: Message):
    user_id = message.from_user.id
    
    # Проверяем админа
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        
        if not user or not user[0]:
            await message.answer("⛔ У тебя нет прав администратора.")
            return
    
    await message.answer(
        "🔧 **ПАНЕЛЬ АДМИНИСТРАТОРА**\n\nВыбери действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        users_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM listings WHERE status = 'active'")
        listings_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM transactions")
        transactions_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE vip_status = 1")
        vip_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT SUM(balance_coins) FROM users")
        total_coins = (await cursor.fetchone())[0] or 0
    
    text = (
        f"📊 **СТАТИСТИКА**\n\n"
        f"👥 Пользователей: **{users_count}**\n"
        f"👑 VIP: **{vip_count}**\n"
        f"📦 Активных лотов: **{listings_count}**\n"
        f"💳 Всего сделок: **{transactions_count}**\n"
        f"💰 Монет в системе: **{total_coins}**"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

# ========== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ ==========
@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery):
    from .config import WEBSITE_URL, VIP_CHAT_LINK
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_keyboard(WEBSITE_URL, VIP_CHAT_LINK)
    )