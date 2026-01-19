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
                # Кам кардани миқдор ва сабти фурӯш
                cursor.execute("UPDATE products SET qty = qty - 1 WHERE code=?", (code,))
                cursor.execute("INSERT INTO sales (name, sell_price, profit, date, code) VALUES (?,?,?,?,?)",
                               (name, sell, sell-buy, datetime.now().strftime("%Y-%m-%d"), code))
                conn.commit()
                conn.close()
                return jsonify({'status': 'ok', 'name': name, 'price': sell})
            conn.close()
            return jsonify({'status': 'error', 'message': 'Маҳсулот дар склад тамом шуд'})
        
        conn.close()
        return jsonify({'status': 'error', 'message': 'Мол дар база нест'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# --- ФАРМОНҲОИ БОТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Тугмаҳои WebApp
    btn_sale = types.KeyboardButton("🟢 ФУРӮШ (КАССА)", web_app=types.WebAppInfo(SCANNER_URL))
    btn_add = types.KeyboardButton("🔵 ҚАБУЛИ МОЛ", web_app=types.WebAppInfo(SCANNER_URL + "?mode=add"))
    # Тугмаҳои ҳисобот
    markup.add(btn_sale, btn_add)
    markup.add("📊 Ҳисобот", "📅 Моҳона")
    markup.add("📦 Склад", "🔙 Бозгашт")
    
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}!\nСистемаи савдо омода аст. Интихоб кунед:", reply_markup=markup)

# ҚАБУЛИ МОЛ АЗ СКАНЕР
@bot.message_handler(content_types=['web_app_data'])
def handle_web_data(message):
    code = message.web_app_data.data
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products WHERE code=?", (code,))
    res = cursor.fetchone(); conn.close()
    
    if res:
        bot.send_message(message.chat.id, f"📦 Мол: {res[0]}\nМиқдор дар склад: {res[1]}\n\nЧанд адад илова кунам?")
        bot.register_next_step_handler(message, lambda m: update_qty(m, code))
    else:
        bot.send_message(message.chat.id, f"🆕 Нав: {code}\nНоми молро нависед:")
        bot.register_next_step_handler(message, lambda m: get_name(m, code))

def update_qty(message, code):
    if message.text.isdigit():
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("UPDATE products SET qty = qty + ? WHERE code=?", (int(message.text), code))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, "✅ Склад нав шуд!")
    else: bot.send_message(message.chat.id, "❌ Танҳо рақам фиристед!")

def get_name(message, code):
    name = message.text
    bot.send_message(message.chat.id, f"Барои '{name}' нависед: Харид Фурӯш Миқдор\nМисол: 10 15 50")
    bot.register_next_step_handler(message, lambda m: save_product(m, code, name))

def save_product(message, code, name):
    try:
        parts = message.text.split()
        b, s, q = float(parts[0]), float(parts[1]), int(parts[2])
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("INSERT INTO products VALUES (?,?,?,?,?)", (code, name, b, s, q))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, "✅ Мол бо муваффақият захира шуд!")
    except:
        bot.send_message(message.chat.id, "❌ Хато! Мисол: 10 15 50")

# ҲИСОБОТИ ИМРӮЗА
@bot.message_handler(func=lambda m: m.text == "📊 Ҳисобот")
def show_report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date=?", (today,))
    res = cursor.fetchone(); conn.close()
    cash = res[0] if res[0] else 0
    profit = res[1] if res[1] else 0
    bot.send_message(message.chat.id, f"📊 ИМРӮЗ ({today}):\n🛍 Фурӯш: {res[2]} адад\n💵 Касса: {cash} смн\n💎 Фоида: {profit} смн")

# ҲИСОБОТИ МОҲОНА
@bot.message_handler(func=lambda m: m.text == "📅 Моҳона")
def show_month_report(message):
    month = datetime.now().strftime("%Y-%m")
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date LIKE ?", (f"{month}%",))
    res = cursor.fetchone(); conn.close()
    cash = res[0] if res[0] else 0
    profit = res[1] if res[1] else 0
    bot.send_message(message.chat.id, f"📅 ДАР МОҲИ ҶОРӢ:\n🛍 Фурӯш: {res[2]} адад\n💵 Касса: {cash} смн\n💎 Фоида: {profit} смн")

# СКЛАД
@bot.message_handler(func=lambda m: m.text == "📦 Склад")
def stock(message):
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name, qty, sell FROM products"); rows = cursor.fetchall(); conn.close()
    if not rows:
        bot.send_message(message.chat.id, "Склад холӣ аст.")
        return
    res = "📦 ҲОЛАТИ СКЛАД:\n\n" + "\n".join([f"• {r[0]}: {r[1]} дона ({r[2]} смн)" for r in rows])
    bot.send_message(message.chat.id, res)

# БОЗГАШТИ МОЛ
@bot.message_handler(func=lambda m: m.text == "🔙 Бозгашт")
def ask_return(message):
    bot.send_message(message.chat.id, "Штрих-коди молро фиристед, то онро ба склад баргардонам:")
    bot.register_next_step_handler(message, process_return)

def process_return(message):
    code = message.text
    conn = get_db(); cursor = conn.cursor()
    # Ёфтани фурӯши охирин бо ин код
    cursor.execute("SELECT id, name FROM sales WHERE code=? ORDER BY id DESC LIMIT 1", (code,))
    res = cursor.fetchone()
    if res:
        cursor.execute("DELETE FROM sales WHERE id=?", (res[0],))
        cursor.execute("UPDATE products SET qty = qty + 1 WHERE code=?", (code,))
        conn.commit(); conn.close()
        bot.send_message(message.chat.id, f"✅ Мол ба склад баргашт: {res[1]}")
    else:
        conn.close()
        bot.send_message(message.chat.id, "❌ Чунин фурӯш ёфт нашуд.")

# --- ЗАПУСК ---
@app.route('/')
def home(): return "Бот фаъол аст!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    init_db()
    Thread(target=run_flask).start()
    bot.polling(none_stop=True)
