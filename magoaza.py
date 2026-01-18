import telebot, sqlite3
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread
from datetime import datetime

# --- ТАНЗИМОТ ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# --- КОР БО БАЗАИ МАЪЛУМОТ ---
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

# --- API БАРОИ СКАНЕРИ ФУРӮШ (WEBAPP) ---
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
            cursor.execute("UPDATE products SET qty = qty - 1 WHERE code = ?", (code,))
            cursor.execute("INSERT INTO sales (name, sell_price, profit, date) VALUES (?, ?, ?, ?)", 
                           (name, sell, sell - buy, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok', 'name': name, 'price': sell})
        conn.close()
        return jsonify({'status': 'out_of_stock'})
    
    conn.close()
    return jsonify({'status': 'new', 'code': code})

@app.route('/')
def home():
    return "Сервер фаъол аст!"

# --- ФАРМОНҲОИ ТЕЛЕГРАМ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Режими Фурӯш (саҳифаи стандартӣ)
    web_app_sale = types.WebAppInfo(SCANNER_URL)
    # Режими Қабул (бо иловаи параметр дар URL)
    web_app_add = types.WebAppInfo(SCANNER_URL + "?mode=add")
    
    markup.add(
        types.KeyboardButton("🟢 ФУРӮШ (КАССА)", web_app=web_app_sale),
        types.KeyboardButton("🔵 ҚАБУЛИ МОЛ (ДОБ)", web_app=web_app_add),
        types.KeyboardButton("📊 Ҳисоботи имрӯза"),
        types.KeyboardButton("📦 Склад")
    )
    bot.send_message(message.chat.id, "Хуш омадед! Режими кориро интихоб кунед:", reply_markup=markup)

# --- МАНТИҚИ ҚАБУЛИ МОЛ (WEB_APP_DATA) ---
@bot.message_handler(content_types=['web_app_data'])
def handle_restock(message):
    code = message.web_app_data.data
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products WHERE code=?", (code,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        name, qty = res
        msg = bot.send_message(message.chat.id, f"📦 Мол: {name}\nДар склад: {qty} адад.\nБоз чанд адад омад? (Танҳо рақам)")
        bot.register_next_step_handler(msg, lambda m: update_qty(m, code))
    else:
        msg = bot.send_message(message.chat.id, f"🆕 Моли нав!\nКод: {code}\nНоми молро нависед:")
        bot.register_next_step_handler(msg, lambda m: get_new_name(m, code))

def update_qty(message, code):
    try:
        add_qty = int(message.text)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET qty = qty + ? WHERE code = ?", (add_qty, code))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Миқдор нав карда шуд!")
    except:
        bot.send_message(message.chat.id, "❌ Хато! Танҳо рақам ворид кунед.")

def get_new_name(message, code):
    name = message.text
    msg = bot.send_message(message.chat.id, f"Маълумоти '{name}'-ро нависед:\nХарид Фурӯш Миқдор\nМисол: 10 15 100")
    bot.register_next_step_handler(msg, lambda m: save_new_product(m, code, name))

def save_new_product(message, code, name):
    try:
        buy, sell, qty = map(float, message.text.split())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?)", (code, name, buy, sell, int(qty)))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Моли нав илова шуд: {name}")
    except:
        bot.send_message(message.chat.id, "❌ Хато! Форматро риоя кунед (10 15 100).")

# --- ҲИСОБОТ ВА СКЛАД ---
@bot.message_handler(func=lambda m: m.text == "📊 Ҳисоботи имрӯза")
def show_report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date=?", (today,))
    res = cursor.fetchone()
    conn.close()
    
    sum_sell = res[0] if res[0] else 0
    sum_profit = res[1] if res[1] else 0
    count = res[2]
    
    bot.send_message(message.chat.id, f"📊 Ҳисоботи имрӯз ({today}):\n\n🛍 Фурӯш: {count} адад\n💵 Касса: {sum_sell} смн\n💎 Фоида: {sum_profit} смн")

@bot.message_handler(func=lambda m: m.text == "📦 Склад")
def show_stock(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty, sell FROM products WHERE qty > 0")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(message.chat.id, "Склад холӣ аст.")
        return
        
    res = "📦 Боқимондаи молҳо:\n\n"
    for r in rows:
        res += f"• {r[0]}: {r[1]} адад (Нарх: {r[2]} смн)\n"
    
    bot.send_message(message.chat.id, res)

# --- ИҶРОИШИ СЕРВЕР ---
def run():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    init_db()
    Thread(target=run).start()
    bot.polling(none_stop=True)
