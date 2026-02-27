import aiosqlite
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shizogp.db')

async def init_db():
    """Инициализация всех таблиц"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance_coins INTEGER DEFAULT 0,
                balance_crypto REAL DEFAULT 0,
                vip_status INTEGER DEFAULT 0,
                vip_until DATETIME,
                referrer_id INTEGER,
                steam_id TEXT,
                steam_username TEXT,
                steam_avatar TEXT,
                rating REAL DEFAULT 5.0,
                rating_count INTEGER DEFAULT 0,
                total_sales INTEGER DEFAULT 0,
                total_purchases INTEGER DEFAULT 0,
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_visit DATETIME,
                is_admin INTEGER DEFAULT 0,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица объявлений (скины на продажу)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                skin_name TEXT,
                quality TEXT,
                price_usd REAL,
                price_rub INTEGER,
                steam_link TEXT,
                image_url TEXT,
                float_value REAL,
                pattern TEXT,
                status TEXT DEFAULT 'active',
                views INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица сделок
        await db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER,
                buyer_id INTEGER,
                seller_id INTEGER,
                amount_usd REAL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                buyer_rating INTEGER,
                seller_rating INTEGER,
                FOREIGN KEY (listing_id) REFERENCES listings (id),
                FOREIGN KEY (buyer_id) REFERENCES users (user_id),
                FOREIGN KEY (seller_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица отзывов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                transaction_id INTEGER,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_user_id) REFERENCES users (user_id),
                FOREIGN KEY (to_user_id) REFERENCES users (user_id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')
        
        # Таблица уведомлений
        await db.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                title TEXT,
                message TEXT,
                data TEXT,
                is_read INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        await db.commit()

async def get_user(user_id):
    """Получить данные пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return await cursor.fetchone()

async def create_user(user_id, username, full_name, referrer_id=None):
    """Создать нового пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем существование
        cursor = await db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if await cursor.fetchone():
            return
        
        # Создаём нового пользователя
        await db.execute('''
            INSERT INTO users (user_id, username, full_name, balance_coins, referrer_id, last_visit)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, full_name, 100, referrer_id))
        
        # Начисляем бонус за реферала
        if referrer_id:
            await db.execute('''
                UPDATE users SET balance_coins = balance_coins + 50 WHERE user_id = ?
            ''', (referrer_id,))
        
        await db.commit()
        return True

async def update_balance(user_id, amount):
    """Изменить баланс пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE users SET balance_coins = balance_coins + ? WHERE user_id = ?
        ''', (amount, user_id))
        await db.commit()

async def add_listing(seller_id, skin_name, quality, price_usd, steam_link):
    """Добавить объявление о продаже"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO listings (seller_id, skin_name, quality, price_usd, steam_link)
            VALUES (?, ?, ?, ?, ?)
        ''', (seller_id, skin_name, quality, price_usd, steam_link))
        await db.commit()
        return cursor.lastrowid

async def get_active_listings(limit=10):
    """Получить активные объявления"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT l.*, u.username as seller_name, u.rating 
            FROM listings l
            JOIN users u ON l.seller_id = u.user_id
            WHERE l.status = 'active'
            ORDER BY l.created_at DESC
            LIMIT ?
        ''', (limit,))
        return await cursor.fetchall()

async def buy_listing(listing_id, buyer_id):
    """Купить скин (создать сделку)"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем информацию о лоте
        cursor = await db.execute('''
            SELECT seller_id, price_usd FROM listings 
            WHERE id = ? AND status = 'active'
        ''', (listing_id,))
        listing = await cursor.fetchone()
        
        if not listing:
            return False, "Лот не найден"
        
        seller_id, price = listing
        
        # Проверяем баланс покупателя
        cursor = await db.execute('SELECT balance_coins FROM users WHERE user_id = ?', (buyer_id,))
        buyer = await cursor.fetchone()
        
        if not buyer or buyer[0] < price:
            return False, "Недостаточно средств"
        
        # Создаём транзакцию
        await db.execute('''
            INSERT INTO transactions (listing_id, buyer_id, seller_id, amount_usd, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (listing_id, buyer_id, seller_id, price))
        
        # Обновляем статус лота
        await db.execute('UPDATE listings SET status = \'sold\' WHERE id = ?', (listing_id,))
        
        # Списание денег у покупателя и зачисление продавцу
        await db.execute('UPDATE users SET balance_coins = balance_coins - ? WHERE user_id = ?', (price, buyer_id))
        await db.execute('UPDATE users SET balance_coins = balance_coins + ? WHERE user_id = ?', (price, seller_id))
        
        await db.commit()
        return True, "Покупка успешна"

async def add_review(from_user_id, to_user_id, transaction_id, rating, comment):
    """Добавить отзыв"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO reviews (from_user_id, to_user_id, transaction_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        ''', (from_user_id, to_user_id, transaction_id, rating, comment))
        
        # Обновляем рейтинг пользователя
        cursor = await db.execute('SELECT AVG(rating) FROM reviews WHERE to_user_id = ?', (to_user_id,))
        avg_rating = (await cursor.fetchone())[0]
        
        cursor = await db.execute('SELECT COUNT(*) FROM reviews WHERE to_user_id = ?', (to_user_id,))
        count = (await cursor.fetchone())[0]
        
        await db.execute('''
            UPDATE users SET rating = ?, rating_count = ? WHERE user_id = ?
        ''', (avg_rating, count, to_user_id))
        
        await db.commit()

async def activate_vip(user_id):
    """Активировать VIP статус"""
    async with aiosqlite.connect(DB_PATH) as db:
        vip_until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        await db.execute('''
            UPDATE users SET vip_status = 1, vip_until = ? WHERE user_id = ?
        ''', (vip_until, user_id))
        await db.commit()