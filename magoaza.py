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

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, profit REAL, date TEXT)''')
    conn.commit()
    conn.close()

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
        conn.close()
        return jsonify({'status': 'error', 'message': 'Тамом шуд'})
    conn.close()
    return jsonify({'status': 'error', 'message': 'Мол нест'})

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    sale_web = types.WebAppInfo(SCANNER_URL)
    add_web = types.WebAppInfo(SCANNER_URL + "?mode=add")
    markup.add(
        types.KeyboardButton("🟢 ФУРӮШ (КАССА)", web_app=sale_web),
        types.KeyboardButton("🔵 ҚАБУЛИ МОЛ (ДОБ)", web_app=add_web),
        types.KeyboardButton("📊 Ҳисоботи имрӯза"),
        types.KeyboardButton("📦 Склад")
    )
    bot.send_message(message.chat.id, "Интихоб кунед:", reply_markup=markup)

# --- ИН ҶО ФУНКСИЯҲОИ ТУГМАҲОИ ШУМО КИ КОР НАМЕКАРДАНД ---
@bot.message_handler(func=lambda m: m.text == "📊 Ҳисоботи имрӯза")
def show_report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date=?", (today,))
    res = cursor.fetchone()
    conn.close()
    cash = res[0] if res[0] else 0
    profit = res[1] if res[1] else 0
    bot.send_message(message.chat.id, f"📊 Имрӯз:\n🛍 Фурӯш: {res[2]} адад\n💵 Касса: {cash} смн\n💎 Фоида: {profit} смн")

@bot.message_handler(func=lambda m: m.text == "📦 Склад")
def show_stock(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty, sell FROM products")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        bot.send_message(message.chat.id, "Склад холӣ аст.")
    else:
        res = "📦 Склад:\n" + "\n".join([f"• {r[0]}: {r[1]} дона ({r[2]} смн)" for r in rows])
        bot.send_message(message.chat.id, res)

# --- МАНТИҚИ ҚАБУЛИ МОЛ ---
@bot.message_handler(content_types=['web_app_data'])
def handle_add(message):
    code = message.web_app_data.data
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name FROM products WHERE code=?", (code,))
    res = cursor.fetchone(); conn.close()
    if res:
        bot.send_message(message.chat.id, f"📦 Мол: {res[0]}\nЧанд адад илова кунам?")
        bot.register_next_step_handler(message, lambda m: update_stock(m, code))
    else:
        bot.send_message(message.chat.id, f"🆕 Моли нав: {code}\nНомашро нависед:")
        bot.register_next_step_handler(message, lambda m: get_new_name(m, code))

def update_stock(message, code):
    try:
        q = int(message.text)
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("UPDATE products SET qty=qty+? WHERE code=?", (q, code))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, "✅ Склад нав шуд!")
    except: bot.send_message(message.chat.id, "Танҳо рақам нависед!")

def get_new_name(message, code):
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
    except: bot.send_message(message.chat.id, "Хато!")

@app.route('/')
def h(): return "OK"

def run(): app.run(host='0.0.0.0', port=8080)
if __name__ == "__main__":
    init_db()
    Thread(target=run).start()
    bot.polling(none_stop=True)
