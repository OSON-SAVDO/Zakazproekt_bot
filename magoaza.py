import telebot
import sqlite3
import json
from telebot import types
from datetime import datetime

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)

def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Оғози база
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)''')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_sale = types.KeyboardButton("🛒 СКАНЕР", web_app=types.WebAppInfo(SCANNER_URL))
    markup.add(btn_sale)
    bot.send_message(message.chat.id, "Хуш омадед! Барои оғоз тугмаи СКАНЕР-ро пахш кунед:", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        
        if data['action'] == 'receive':
            code = data['code']
            msg = bot.send_message(message.chat.id, 
                f"📦 **Моли нав скан шуд:** `{code}`\n\n"
                "Лутфан маълумотро чунин фиристед:\n"
                "`Ном, Нархи_харид, Нархи_фурӯш, Миқдор`", 
                parse_mode="Markdown")
            bot.register_next_step_handler(msg, lambda m: save_product(m, code))
            
        elif data['action'] == 'sale':
            items = data['items']
            total_sum = 0
            with get_db() as conn:
                for code, info in items.items():
                    summ = info['qty'] * info['price']
                    total_sum += summ
                    conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                                 (info['name'], summ, datetime.now().strftime("%d.%m.%Y %H:%M")))
                conn.commit()
            bot.send_message(message.chat.id, f"✅ Фурӯш қабул шуд!\n💰 Ҷамъ: {total_sum} смн")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Хатогӣ: {e}")

def save_product(message, code):
    try:
        parts = [i.strip() for i in message.text.split(',')]
        name, buy, sell, qty = parts
        with get_db() as conn:
            conn.execute("INSERT OR REPLACE INTO products (code, name, buy, sell, qty) VALUES (?,?,?,?,?)", 
                         (code, name, float(buy), float(sell), int(qty)))
            conn.commit()
        bot.send_message(message.chat.id, f"✅ Мол илова шуд: {name}")
    except:
        bot.send_message(message.chat.id, "❌ Хато дар формат! Мисол: Кола, 5, 8, 50")

if __name__ == "__main__":
    bot.polling(none_stop=True)
