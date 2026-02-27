from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_keyboard(website_url: str, vip_chat_link: str):
    """Главное меню"""
    buttons = [
        [InlineKeyboardButton(
            text="🛒 Магазин", 
            web_app=WebAppInfo(url=f"{website_url}/webapp")
        )],
        [
            InlineKeyboardButton(text="💸 Продать скин", callback_data="sell"),
            InlineKeyboardButton(text="📦 Сделки", callback_data="my_deals")
        ],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
            InlineKeyboardButton(text="🤝 Рефералы", callback_data="referral")
        ],
        [InlineKeyboardButton(text="👑 VIP чат", url=vip_chat_link)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_keyboard():
    """Кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀ Назад", callback_data="main_menu")]
    ])

def get_listings_keyboard(listings, page=0):
    """Клавиатура со списком скинов"""
    builder = InlineKeyboardBuilder()
    
    for listing in listings:
        builder.row(InlineKeyboardButton(
            text=f"{listing['skin_name']} - ${listing['price_usd']}",
            callback_data=f"view_{listing['id']}"
        ))
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀", callback_data=f"page_{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text="📊", callback_data="stats"))
    nav_buttons.append(InlineKeyboardButton(text="▶", callback_data=f"page_{page+1}"))
    
    builder.row(*nav_buttons)
    builder.row(InlineKeyboardButton(text="◀ Назад", callback_data="main_menu"))
    
    return builder.as_markup()

def get_listing_detail_keyboard(listing_id):
    """Клавиатура для детального просмотра"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Купить", callback_data=f"buy_{listing_id}"),
        InlineKeyboardButton(text="📞 Спросить", callback_data=f"ask_{listing_id}")
    )
    builder.row(InlineKeyboardButton(text="◀ Назад к списку", callback_data="listings"))
    return builder.as_markup()

def get_admin_keyboard():
    """Админская клавиатура"""
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="admin_add_balance")],
        [InlineKeyboardButton(text="👑 Выдать VIP", callback_data="admin_give_vip")],
        [InlineKeyboardButton(text="📦 Сделки", callback_data="admin_transactions")],
        [InlineKeyboardButton(text="◀ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)