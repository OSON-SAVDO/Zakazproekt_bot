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

# Базаро омода мекунем
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)''')

@bot.message_handler(commands=['start'])
def start(message):
    # ReplyKeyboardRemove барои тоза кардани тугмаҳои кӯҳна
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Танҳо 3 тугмаи асосиро мемонем
    btn_sale = types.KeyboardButton("🚀 СКАНЕРИ ФУРӮШ", web_app=types.WebAppInfo(SCANNER_URL))
    btn_excel = types.KeyboardButton("📦 ҚАБУЛИ МОЛ (EXCEL)")
    btn_report = types.KeyboardButton("📊 ҲИСОБОТ")
    
    markup.add(btn_sale)
    markup.add(btn_excel, btn_report)
    
    bot.send_message(message.chat.id, "Хуш омадед! Режимро интихоб кунед:", reply_markup=markup)

# --- ҚАБУЛИ МОЛ АЗ EXCEL ---
@bot.message_handler(func=lambda message: message.text == "📦 ҚАБУЛИ МОЛ (EXCEL)")
def excel_import_start(message):
    msg = bot.send_message(message.chat.id, 
        "📊 **МАЪЛУМОТРО АЗ EXCEL ФИРИСТЕД**\n\n"
        "Маълумотро копя кунед ва инҷо 'Paste' кунед.\n"
        "Формат: `Штрихкод, Ном, Нарх_харид, Нарх_фурӯш, Миқдор`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_excel_text)

def process_excel_text(message):
    lines = message.text.split('\n')
    added = 0
    with get_db() as conn:
        for line in lines:
            try:
                parts = [p.strip() for p in line.replace('|', ',').split(',')]
                if len(parts) >= 5:
                    conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?)", 
                                 (parts[0], parts[1], float(parts[2]), float(parts[3]), int(parts[4])))
                    added += 1
            except: continue
        conn.commit()
    bot.send_message(message.chat.id, f"✅ Илова шуд: {added} мол")

# --- ҚАБУЛИ ФУРӮШ АЗ WEB APP ---
@bot.message_handler(content_types=['web_app_data'])
def handle_app_data(message):
    data = json.loads(message.web_app_data.data)
    if data.get('action') == 'sale':
        items = data['items']
        total = 0
        with get_db() as conn:
            for code, info in items.items():
                summ = info['qty'] * info['price']
                total += summ
                conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                             (info['name'], summ, datetime.now().strftime("%d.%m.%Y %H:%M")))
                conn.execute("UPDATE products SET qty = qty - ? WHERE code = ?", (info['qty'], code))
            conn.commit()
        bot.send_message(message.chat.id, f"💰 Фурӯш қабул шуд: {total} смн")

if __name__ == "__main__":
    bot.polling(none_stop=True)
