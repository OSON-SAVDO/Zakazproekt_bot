import telebot, sqlite3
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread
from datetime import datetime

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    return conn

# --- API БАРОИ ФУРӮШ (БЕ БАСТА ШУДАНИ САҲИФА) ---
@app.route('/scan', methods=['POST'])
def scan_api():
    data = request.json
    code = data.get('code')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, buy, sell, qty FROM products WHERE code=?", (code,))
    res = cursor.fetchone()
    if res:
        name, buy, sell, qty = res
        if qty > 0:
            cursor.execute("UPDATE products SET qty=qty-1 WHERE code=?", (code,))
            cursor.execute("INSERT INTO sales (name, sell_price, profit, date) VALUES (?, ?, ?, ?)", 
                           (name, sell, sell-buy, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok', 'name': name, 'price': sell})
        return jsonify({'status': 'error', 'message': 'Тамом шуд'})
    conn.close()
    return jsonify({'status': 'error', 'message': 'Мол нест'})

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Тугмаи фурӯш (index.html мефаҳмад ки режими фурӯш аст)
    sale_web = types.WebAppInfo(SCANNER_URL)
    # Тугмаи илова (ба URL параметр илова мекунем)
    add_web = types.WebAppInfo(SCANNER_URL + "?mode=add")
    
    markup.add(
        types.KeyboardButton("🟢 ФУРӮШ (КАССА)", web_app=sale_web),
        types.KeyboardButton("🔵 ИЛОВАИ МОЛ (СКЛАД)", web_app=add_web),
        types.KeyboardButton("📊 Ҳисобот"),
        types.KeyboardButton("📦 Склад")
    )
    bot.send_message(message.chat.id, "Хуш омадед! Режимро интихоб кунед:", reply_markup=markup)

# --- МАНТИҚИ ИЛОВАИ МОЛ (ВАҚТЕ САҲИФА БАСТА МЕШАВАД) ---
@bot.message_handler(content_types=['web_app_data'])
def handle_add_product(message):
    code = message.web_app_data.data
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products WHERE code=?", (code,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        bot.send_message(message.chat.id, f"📦 Мол: {res[0]} ҳаст ({res[1]} дона).\nЧанд дона илова кунам?")
        bot.register_next_step_handler(message, lambda m: update_stock(m, code))
    else:
        bot.send_message(message.chat.id, f"🆕 Моли нав: {code}\nНомашро нависед:")
        bot.register_next_step_handler(message, lambda m: get_name(m, code))

def update_stock(message, code):
    try:
        qty = int(message.text)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET qty=qty+? WHERE code=?", (qty, code))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, "✅ Склад нав шуд!")
    except: bot.send_message(message.chat.id, "❌ Танҳо рақам нависед!")

def get_name(message, code):
    name = message.text
    bot.send_message(message.chat.id, f"Барои '{name}' нависед: Харид Фурӯш Миқдор\nМисол: 10 15 50")
    bot.register_next_step_handler(message, lambda m: save_product(m, code, name))

def save_product(message, code, name):
    try:
        b, s, q = map(float, message.text.split())
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("INSERT INTO products VALUES (?,?,?,?,?)", (code, name, b, s, int(q)))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, "✅ Илова шуд!")
    except: bot.send_message(message.chat.id, "❌ Хато дар ворид кардан!")

@app.route('/')
def h(): return "OK"

def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()
bot.polling(none_stop=True)
