import hashlib
import hmac
import json
from datetime import datetime

def verify_telegram_auth(init_data: str, bot_token: str):
    """Проверка подписи от Telegram"""
    data = {}
    for item in init_data.split('&'):
        key, value = item.split('=')
        data[key] = value
    
    if 'hash' not in data:
        return None
    
    hash_check = data.pop('hash')
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))
    
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if computed_hash != hash_check:
        return None
    
    return data.get('user')

def format_number(num):
    """Форматирование больших чисел"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def escape_markdown(text):
    """Экранирование спецсимволов Markdown"""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text