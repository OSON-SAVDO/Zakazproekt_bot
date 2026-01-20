import telebot, sqlite3, json
from telebot import types
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
from datetime import datetime

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/" # URL-и GitHub

bot = telebot.TeleBot(TOKEN)
app = Flask('')
CORS(app)

def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Сохтани база
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, profit REAL, date TEXT)''')

@app.route('/api/get_product', methods=['POST'])
def get_product():
    data = request.json
    code = data.get('code')
    with get_db() as conn:
        res = conn.execute("SELECT name, sell FROM products WHERE code=?", (code,)).fetchone()
    if res:
        return jsonify({'status': 'ok', 'name': res['name'], 'price': res['sell']})
    return jsonify({'status': 'error'})

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("🛒 СКАНЕР (ФУРӮШ)", web_app=types.WebAppInfo(f"{SCANNER_URL}?mode=sale")),
        types.KeyboardButton("📦 СКАНЕР (ҚАБУЛ)", web_app=types.WebAppInfo(f"{SCANNER_URL}?mode=receive"))
    )
    markup.row("📊 Ҳисобот", "📅 Моҳона")
    markup.row("🏠 Склад", "🔙 Бозгашт")
    bot.send_message(message.chat.id, "Интихоб кунед:", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_data(message):
    data = json.loads(message.web_app_data.data)
    
    if data.get('action') == 'receive':
        code = data['code']
        msg = bot.send_message(message.chat.id, f"📦 Мол: `{code}`\nВорид кунед: `Ном, Нархи_харид, Нархи_фурӯш, Миқдор`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: save_product(m, code))
        
    elif data.get('action') == 'sale':
        items = data['items']
        total = 0
        with get_db() as conn:
            for code, info in items.items():
                summ = info['qty'] * info['price']
                total += summ
                conn.execute("UPDATE products SET qty = qty - ? WHERE code = ?", (info['qty'], code))
                conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                             (info['name'], summ, datetime.now().strftime("%Y-%m-%d %H:%M")))
        bot.send_message(message.chat.id, f"✅ Фурӯш анҷом ёфт!\n💰 Ҷамъ: {total} смн")

def save_product(message, code):
    try:
        name, buy, sell, qty = [i.strip() for i in message.text.split(',')]
        with get_db() as conn:
            conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?)", (code, name, float(buy), float(sell), int(qty)))
        bot.send_message(message.chat.id, f"✅ Мол илова шуд: {name}")
    except:
        bot.send_message(message.chat.id, "❌ Хато! Намуна: Оби ҷав, 5, 7, 100")

def run(): app.run(host='0.0.0.0', port=8080)
if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
