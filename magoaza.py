import telebot, sqlite3, json
from telebot import types
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
from datetime import datetime

# --- ТАНЗИМОТ ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
# Суроғаи GitHub-и шумо, ки дар он index.html ҷойгир аст
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Эҷоди база ҳангоми оғоз
def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS products 
                        (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)''')
        conn.commit()

# --- API БАРОИ СКАНЕР ---
@app.route('/api/get_product', methods=['POST'])
def get_product():
    try:
        data = request.json
        code = data.get('code')
        with get_db() as conn:
            res = conn.execute("SELECT name, sell FROM products WHERE code=?", (code,)).fetchone()
        if res:
            return jsonify({'status': 'ok', 'name': res['name'], 'price': res['sell']})
        return jsonify({'status': 'error', 'message': 'Маҳсулот ёфт нашуд'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# --- БОТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Тугмаҳо барои Web App
    btn_sale = types.KeyboardButton("🛒 СКАНЕР (ФУРӮШ)", web_app=types.WebAppInfo(f"{SCANNER_URL}?mode=sale"))
    btn_receive = types.KeyboardButton("📦 СКАНЕР (ҚАБУЛ)", web_app=types.WebAppInfo(f"{SCANNER_URL}?mode=receive"))
    
    markup.add(btn_sale, btn_receive)
    markup.add("📊 Ҳисобот", "📅 Моҳона")
    markup.add("🏠 Склад", "🔙 Бозгашт")
    
    bot.send_message(message.chat.id, "Хуш омадед! Режимро интихоб кунед:", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_data(message):
    try:
        raw_data = json.loads(message.web_app_data.data)
        
        if raw_data.get('action') == 'receive':
            code = raw_data['code']
            msg = bot.send_message(message.chat.id, f"📦 Мол скан шуд: `{code}`\n\nВорид кунед: `Ном, Нархи_харид, Нархи_фурӯш, Миқдор` (бо вергул)")
            bot.register_next_step_handler(msg, lambda m: save_product(m, code))
            
        elif raw_data.get('action') == 'sale':
            items = raw_data['items']
            total = 0
            with get_db() as conn:
                for code, info in items.items():
                    summ = info['qty'] * info['price']
                    total += summ
                    # Навсозии миқдор дар склад
                    conn.execute("UPDATE products SET qty = qty - ? WHERE code = ?", (info['qty'], code))
                    # Сабти фурӯш
                    conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                                 (info['name'], summ, datetime.now().strftime("%d.%m.%Y %H:%M")))
                conn.commit()
            bot.send_message(message.chat.id, f"✅ Фурӯш анҷом ёфт!\n💰 Ҷамъ: {total} смн")
    except Exception as e:
        bot.send_message(message.chat.id, f"Хато дар коркарди маълумот: {e}")

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
        bot.send_message(message.chat.id, "❌ Хато дар формат! Мисол: Кола 1л, 5, 8, 50")

def run():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    init_db()
    Thread(target=run).start()
    bot.polling(none_stop=True)
