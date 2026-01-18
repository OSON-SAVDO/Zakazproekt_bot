import telebot, sqlite3
from telebot import types
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
from datetime import datetime
import os

# --- ТАНЗИМОТ ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
# Суроғаи саҳифаи шумо дар GitHub
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')
CORS(app)

# --- КОР БО БАЗАИ МАЪЛУМОТ ---
def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Таблицаи молҳо
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    # Таблицаи фурӯш
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, profit REAL, date TEXT, code TEXT)''')
    conn.commit()
    conn.close()

# --- API БАРОИ СКАНЕРИ ФУРӮШ ---
@app.route('/scan', methods=['POST'])
def scan_api():
    try:
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
                cursor.execute("INSERT INTO sales (name, sell_price, profit, date, code) VALUES (?, ?, ?, ?, ?)", 
                               (name, sell, sell-buy, datetime.now().strftime("%Y-%m-%d"), code))
                conn.commit()
                conn.close()
                return jsonify({'status': 'ok', 'name': name, 'price': sell, 'code': code})
            conn.close()
            return jsonify({'status': 'error', 'message': 'Ин мол дар склад тамом шуд'})
        
        conn.close()
        return jsonify({'status': 'error', 'message': 'Мол ёфт нашуд'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# API БАРОИ НЕСТ КАРДАНИ МОЛ АЗ ЧЕК (❌)
@app.route('/remove_item', methods=['POST'])
def remove_item():
    try:
        data = request.json
        code = data.get('code')
        conn = get_db(); cursor = conn.cursor()
        # Молро ба склад бармегардонем
        cursor.execute("UPDATE products SET qty=qty+1 WHERE code=?", (code,))
        # Фурӯши охиринро нест мекунем
        cursor.execute("DELETE FROM sales WHERE id = (SELECT id FROM sales WHERE code=? ORDER BY id DESC LIMIT 1)", (code,))
        conn.commit(); conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# --- ФАРМОНҲОИ ТЕЛЕГРАМ БОТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Тугмаҳо барои WebApp
    btn_sale = types.KeyboardButton("🟢 ФУРӮШ (КАССА)", web_app=types.WebAppInfo(SCANNER_URL))
    btn_add = types.KeyboardButton("🔵 ҚАБУЛИ МОЛ (ДОБ)", web_app=types.WebAppInfo(SCANNER_URL + "?mode=add"))
    # Тугмаҳои оддӣ
    btn_report = types.KeyboardButton("📊 Ҳисоботи имрӯза")
    btn_stock = types.KeyboardButton("📦 Склад")
    
    markup.add(btn_sale, btn_add)
    markup.add(btn_report, btn_stock)
    bot.send_message(message.chat.id, "Хуш омадед! Интихоб кунед:", reply_markup=markup)

# ИЛОВАИ ДАСТӢ: Агар рақами штрих-кодро нависед
@bot.message_handler(func=lambda m: m.text.isdigit() and len(m.text) >= 4)
def manual_input(message):
    code = message.text
    process_barcode(message, code)

# ҲИСОБОТ
@bot.message_handler(func=lambda m: m.text == "📊 Ҳисоботи имрӯза")
def show_report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date=?", (today,))
    res = cursor.fetchone(); conn.close()
    cash = res[0] if res[0] else 0
    profit = res[1] if res[1] else 0
    bot.send_message(message.chat.id, f"📊 Имрӯз:\n🛍 Фурӯш: {res[2]} адад\n💵 Касса: {cash} смн\n💎 Фоида: {profit} смн")

# СКЛАД
@bot.message_handler(func=lambda m: m.text == "📦 Склад")
def show_stock(message):
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name, qty, sell FROM products")
    rows = cursor.fetchall(); conn.close()
    if not rows:
        bot.send_message(message.chat.id, "Склад холӣ аст.")
    else:
        res = "📦 Склад:\n" + "\n".join([f"• {r[0]}: {r[1]} дона ({r[2]} смн)" for r in rows])
        bot.send_message(message.chat.id, res)

# ҚАБУЛИ МАЪЛУМОТ АЗ СКАНЕРИ "ҚАБУЛИ МОЛ"
@bot.message_handler(content_types=['web_app_data'])
def handle_web_data(message):
    code = message.web_app_data.data
    process_barcode(message, code)

def process_barcode(message, code):
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name FROM products WHERE code=?", (code,))
    res = cursor.fetchone(); conn.close()
    if res:
        bot.send_message(message.chat.id, f"📦 Мол: {res[0]}\nЧанд адад илова кунам?")
        bot.register_next_step_handler(message, lambda m: update_qty(m, code))
    else:
        bot.send_message(message.chat.id, f"🆕 Моли нав: {code}\nНомашро нависед:")
        bot.register_next_step_handler(message, lambda m: get_name(message, code))

def update_qty(message, code):
    try:
        q = int(message.text)
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("UPDATE products SET qty=qty+? WHERE code=?", (q, code))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, "✅ Склад нав шуд!")
    except: bot.send_message(message.chat.id, "❌ Танҳо рақам нависед!")

def get_name(message, code):
    name = message.text
    bot.send_message(message.chat.id, f"Барои '{name}' нависед: Харид Фурӯш Миқдор\nМисол: 10 15 100")
    bot.register_next_step_handler(message, lambda m: save_new(m, code, name))

def save_new(message, code, name):
    try:
        b, s, q = map(float, message.text.split())
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("INSERT INTO products VALUES (?,?,?,?,?)", (code, name, b, s, int(q)))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, "✅ Илова шуд!")
    except: bot.send_message(message.chat.id, "❌ Хато! Намуна: 10 15 100")

# --- ЗАПУСК ---
@app.route('/')
def home(): return "OK"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    init_db()
    Thread(target=run_flask).start()
    bot.polling(none_stop=True)
