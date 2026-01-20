import telebot, sqlite3
from telebot import types
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
from datetime import datetime

# --- ТАНЗИМОТ ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')
CORS(app)

# --- БАЗАИ МАЪЛУМОТ ---
def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False, timeout=10)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, profit REAL, date TEXT, code TEXT)''')
    conn.commit()
    conn.close()

# --- API БАРОИ СКАНЕР ---
@app.route('/api/scan', methods=['POST'])
def scan_api():
    data = request.json
    code = data.get('code')
    mode = data.get('mode') # 'sale' ё 'receive'
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, sell, buy FROM products WHERE code=?", (code,))
    product = cursor.fetchone()
    
    if product:
        name, sell, buy = product
        if mode == 'sale':
            cursor.execute("UPDATE products SET qty = qty - 1 WHERE code=?", (code,))
            cursor.execute("INSERT INTO sales (name, sell_price, profit, date, code) VALUES (?,?,?,?,?)",
                           (name, sell, sell-buy, datetime.now().strftime("%Y-%m-%d"), code))
        else: # Режими қабул
            cursor.execute("UPDATE products SET qty = qty + 1 WHERE code=?", (code,))
        
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok', 'name': name, 'price': sell})
    
    conn.close()
    return jsonify({'status': 'error', 'message': 'Мол дар база нест'})

# --- ФАРМОНҲОИ БОТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_scanner = types.KeyboardButton("📸 СКАНЕР (ФУРӮШ/ҚАБУЛ)", web_app=types.WebAppInfo(SCANNER_URL))
    markup.add(btn_scanner)
    markup.add(types.KeyboardButton("📊 Ҳисобот"), types.KeyboardButton("📅 Моҳона"))
    markup.add(types.KeyboardButton("📦 Склад"), types.KeyboardButton("🔙 Бозгашт"))
    
    bot.send_message(message.chat.id, "Система омода. Сканнерро кушоед:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 Ҳисобот")
def show_report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date=?", (today,))
    res = cursor.fetchone(); conn.close()
    bot.send_message(message.chat.id, f"📊 ИМРӮЗ: {res[2]} фурӯш\n💵 Касса: {res[0] or 0} смн")

@bot.message_handler(func=lambda m: m.text == "📦 Склад")
def stock(message):
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products"); rows = cursor.fetchall(); conn.close()
    res = "📦 СКЛАД:\n" + "\n".join([f"{r[0]}: {r[1]} дона" for r in rows])
    bot.send_message(message.chat.id, res if rows else "Склад холӣ аст")

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    init_db()
    Thread(target=run_flask).start()
    bot.polling(none_stop=True)
