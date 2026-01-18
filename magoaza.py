import telebot, sqlite3, time
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread
from datetime import datetime

# 1. МАЪЛУМОТҲОИ АСОСӢ (API ва СИЛКА)
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# 2. ФУНКСИЯ БАРОИ БАЗАИ МАЪЛУМОТ
def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, profit REAL, date TEXT)''')
    conn.commit()
    conn.close()

# 3. API БАРОИ СКАНЕР (Ин қисмест, ки шумо пурсидед)
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
            new_qty = qty - 1
            cursor.execute("UPDATE products SET qty=? WHERE code=?", (new_qty, code))
            cursor.execute("INSERT INTO sales (name, sell_price, profit, date) VALUES (?, ?, ?, ?)", 
                           (name, sell, sell-buy, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            
            # Ин ҷо мо маълумоти лозимиро ба саҳифаи сканер бармегардонем
            return jsonify({'status': 'ok', 'name': name, 'price': sell})
        else:
            conn.close()
            return jsonify({'status': 'out_of_stock'})
    else:
        conn.close()
        return jsonify({'status': 'new'})

@app.route('/')
def home(): 
    return "Бот ва API фаъоланд!"

# 4. ФАРМОНҲОИ БОТ (TELEGRAM)
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Истифодаи силкаи SCANNER_URL дар тугма
    web_app = types.WebAppInfo(SCANNER_URL)
    markup.add(
        types.KeyboardButton("📸 Сканери Касса", web_app=web_app),
        types.KeyboardButton("📊 Ҳисобот"),
        types.KeyboardButton("📦 Склад")
    )
    bot.send_message(message.chat.id, "Хуш омадед! Сканерро кушоед ва фурӯшро оғоз кунед.", reply_markup=markup)

# Дигар функсияҳои бот (Склад, Ҳисобот ва ғайра)...
@bot.message_handler(func=lambda m: m.text == "📊 Ҳисобот")
def show_report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit) FROM sales WHERE date=?", (today,))
    res = cursor.fetchone()
    conn.close()
    cash = res[0] if res[0] else 0
    profit = res[1] if res[1] else 0
    bot.send_message(message.chat.id, f"📊 Имрӯз:\n💵 Касса: {cash} смн\n💎 Фоида: {profit} смн")

def run():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    init_db()
    Thread(target=run).start()
    bot.polling(none_stop=True)
