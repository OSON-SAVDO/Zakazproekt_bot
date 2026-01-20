import telebot, sqlite3
from telebot import types
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
from datetime import datetime

# --- ТАНЗИМОТ ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
# URL-и GitHub-и шумо
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')
CORS(app)

def get_db():
    return sqlite3.connect('shop.db', check_same_thread=False, timeout=10)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, profit REAL, date TEXT, code TEXT)''')
    conn.commit()
    conn.close()

# API барои сканери фурӯш
@app.route('/api/get_product', methods=['POST'])
def get_product():
    data = request.json
    code = data.get('code')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name, sell FROM products WHERE code=?", (code,))
    res = cursor.fetchone(); conn.close()
    if res:
        return jsonify({'status': 'ok', 'name': res[0], 'price': res[1]})
    return jsonify({'status': 'error', 'message': 'Мол ёфт нашуд'})

# --- МЕНЮИ БОТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Ду тугмаи сканер дар боло
    btn_sale = types.KeyboardButton("🛒 СКАНЕР (ФУРӮШ)", web_app=types.WebAppInfo(SCANNER_URL + "?mode=sale"))
    btn_receive = types.KeyboardButton("📦 СКАНЕР (ҚАБУЛ)", web_app=types.WebAppInfo(SCANNER_URL + "?mode=receive"))
    
    markup.add(btn_sale, btn_receive)
    markup.add("📊 Ҳисобот", "📅 Моҳона")
    markup.add("🏠 Склад", "🔙 Бозгашт")
    
    bot.send_message(message.chat.id, "Хуш омадед! Режимро интихоб кунед:", reply_markup=markup)

# Логикаи Қабул (вақте ки аз Веб-апп маълумот меояд)
@bot.message_handler(content_types=['web_app_data'])
def web_app_handle(message):
    # Агар аз сканери ҚАБУЛ штрих-код ояд
    code = message.web_app_data.data
    msg = bot.send_message(message.chat.id, f"📦 Мол скан шуд: `{code}`\n\nЛутфан маълумотро ворид кунед:\n`Ном, Нархи_харид, Нархи_фурӯш, Миқдор`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: process_add_product(m, code))

def process_add_product(message, code):
    try:
        parts = [i.strip() for i in message.text.split(',')]
        name, buy, sell, qty = parts
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?)", (code, name, float(buy), float(sell), int(qty)))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, f"✅ Мол илова шуд: {name}")
    except:
        bot.send_message(message.chat.id, "❌ Хато дар формат! Мисол: Оби газнок, 2, 4, 50")

# --- ИҶРОИ ФЛАСК ---
def run(): app.run(host='0.0.0.0', port=8080)
if __name__ == "__main__":
    init_db()
    Thread(target=run).start()
    bot.polling(none_stop=True)
