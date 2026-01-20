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
@app.route('/scan', methods=['POST'])
def scan_api():
    try:
        data = request.json
        code = data.get('code')
        mode = data.get('mode')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, buy, sell, qty FROM products WHERE code=?", (code,))
        res = cursor.fetchone()
        
        if res:
            name, buy, sell, qty = res
            if mode == 'sale':
                if qty > 0:
                    cursor.execute("UPDATE products SET qty = qty - 1 WHERE code=?", (code,))
                    cursor.execute("INSERT INTO sales (name, sell_price, profit, date, code) VALUES (?,?,?,?,?)",
                                   (name, sell, sell-buy, datetime.now().strftime("%Y-%m-%d"), code))
                    conn.commit()
                    conn.close()
                    return jsonify({'status': 'ok', 'name': name, 'price': sell})
                else:
                    conn.close()
                    return jsonify({'status': 'error', 'message': 'Тамом шуд'})
            else:
                conn.close()
                return jsonify({'status': 'ok', 'name': name, 'price': sell, 'qty': qty})
        
        conn.close()
        return jsonify({'status': 'error', 'message': 'Мол ёфт нашуд'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# --- ФАРМОНҲОИ БОТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Тугмаи асосии WebApp
    btn_scanner = types.KeyboardButton("📸 СКАНЕР (ФУРӮШ/ҚАБУЛ)", web_app=types.WebAppInfo(SCANNER_URL))
    
    # Илова кардани тугмаи Қабул дар назди Ҳисобот ва Склад
    markup.add(btn_scanner)
    markup.add("📊 Ҳисобот", "📅 Моҳона")
    markup.add("📦 Қабул", "🏠 Склад") # ТУГМАИ НАВ ДАР ИНҶО
    markup.add("🔙 Бозгашт")
    
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}!\nСистема омода аст. Интихоб кунед:", reply_markup=markup)

# --- ФУНКСИЯИ ҚАБУЛИ МОЛ ---
@bot.message_handler(func=lambda m: m.text == "📦 Қабул")
def receive_item(message):
    msg = bot.send_message(message.chat.id, "Лутфан маълумоти молро барои илова кардан фиристед.\nФормат: `коди_мол, ном, нархи_харид, нархи_фурӯш, миқдор`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_receive)

def process_receive(message):
    try:
        # Намуна: 12345, Оби газнок, 2.5, 4, 10
        data = [i.strip() for i in message.text.split(',')]
        code, name, buy, sell, qty = data
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO products (code, name, buy, sell, qty) VALUES (?, ?, ?, ?, ?)",
                       (code, name, float(buy), float(sell), int(qty)))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Мол бо муваффақият қабул шуд:\n📦 Ном: {name}\n🔢 Миқдор: {qty} адад")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Хатогӣ дар формат! Боварӣ ҳосил кунед, ки маълумотро дуруст ворид кардед.\nНамуна: `12345678, Номи мол, 5, 8, 20`", parse_mode="Markdown")

# ҲИСОБОТҲО
@bot.message_handler(func=lambda m: m.text == "📊 Ҳисобот")
def show_report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date=?", (today,))
    res = cursor.fetchone(); conn.close()
    cash = res[0] if res[0] else 0
    profit = res[1] if res[1] else 0
    bot.send_message(message.chat.id, f"📊 ИМРӮЗ ({today}):\n🛍 Фурӯш: {res[2]} адад\n💵 Касса: {cash} смн\n💎 Фоида: {profit} смн")

@bot.message_handler(func=lambda m: m.text == "📅 Моҳона")
def show_month_report(message):
    month = datetime.now().strftime("%Y-%m")
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date LIKE ?", (f"{month}%",))
    res = cursor.fetchone(); conn.close()
    cash = res[0] if res[0] else 0
    profit = res[1] if res[1] else 0
    bot.send_message(message.chat.id, f"📅 ДАР МОҲИ ҶОРӢ:\n🛍 Фурӯш: {res[2]} адад\n💵 Касса: {cash} смн\n💎 Фоида: {profit} смн")

@bot.message_handler(func=lambda m: m.text == "🏠 Склад")
def stock(message):
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name, qty, sell FROM products"); rows = cursor.fetchall(); conn.close()
    if not rows:
        bot.send_message(message.chat.id, "Склад холӣ аст.")
        return
    res = "🏠 ҲОЛАТИ СКЛАД:\n\n" + "\n".join([f"• {r[0]}: {r[1]} дона ({r[2]} смн)" for r in rows])
    bot.send_message(message.chat.id, res)

@bot.message_handler(func=lambda m: m.text == "🔙 Бозгашт")
def ask_return(message):
    bot.send_message(message.chat.id, "Штрих-коди молро фиристед, то онро ба склад баргардонам:")
    bot.register_next_step_handler(message, process_return)

def process_return(message):
    code = message.text
    conn = get_db(); cursor = conn.cursor()
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
