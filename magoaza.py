import telebot, sqlite3, time
from telebot import types
from flask import Flask
from threading import Thread
from datetime import datetime

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# --- БАЗАИ МАЪЛУМОТ (SQLite) ---
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

@app.route('/')
def home(): return "Бот фаъол аст!"

def run(): app.run(host='0.0.0.0', port=8080)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    web_app = types.WebAppInfo(SCANNER_URL)
    markup.add(
        types.KeyboardButton("📸 Сканер", web_app=web_app),
        types.KeyboardButton("📊 Ҳисоботи имрӯза"),
        types.KeyboardButton("➕ Иловаи мол"),
        types.KeyboardButton("📦 Склад")
    )
    bot.send_message(message.chat.id, "Системаи склад ва фурӯш омода аст!", reply_markup=markup)

# --- ИЛОВАИ МОЛ ---
@bot.message_handler(func=lambda m: m.text == "➕ Иловаи мол")
def add_start(message):
    bot.send_message(message.chat.id, "Штрих-кодро нависед (ё сканер кунед):")
    bot.register_next_step_handler(message, get_code)

def get_code(message):
    code = message.text
    bot.send_message(message.chat.id, "Номи мол:")
    bot.register_next_step_handler(message, lambda m: get_name(m, code))

def get_name(message, code):
    name = message.text
    bot.send_message(message.chat.id, "Харид, Фурӯш ва Миқдорро бо фосила нависед (масалан: 10 15 100):")
    bot.register_next_step_handler(message, lambda m: save_product(m, code, name))

def save_product(message, code, name):
    try:
        buy, sell, qty = map(float, message.text.split())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?)", (code, name, buy, sell, int(qty)))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ {name} ба склад илова шуд!")
    except:
        bot.send_message(message.chat.id, "❌ Хато! Танҳо рақамҳоро бо фосила нависед.")

# --- СКАНЕР ВА ФУРӮШ ---
@bot.message_handler(content_types=['web_app_data'])
def handle_scanner(message):
    code = message.web_app_data.data
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
            bot.send_message(message.chat.id, f"✅ Фурӯхта шуд: {name}\n💰 Нарх: {sell}\n📦 Боқӣ: {new_qty} адад")
        else:
            bot.send_message(message.chat.id, f"⚠️ Мол дар склад тамом шуд!")
    else:
        bot.send_message(message.chat.id, f"❌ Мол бо коди {code} ёфт нашуд.")
    conn.close()

# --- ҲИСОБОТҲО ---
@bot.message_handler(func=lambda m: m.text == "📊 Ҳисоботи имрӯза")
def report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date=?", (today,))
    cash, profit, count = cursor.fetchone()
    conn.close()
    
    if count > 0:
        bot.send_message(message.chat.id, f"📊 **Ҳисобот:**\n🛍 Фурӯш: {count} адад\n💵 Касса: {cash} сомонӣ\n💎 Фоида: {profit} сомонӣ", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "Имрӯз фурӯш нашудааст.")

@bot.message_handler(func=lambda m: m.text == "📦 Склад")
def show_stock(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products")
    rows = cursor.fetchall()
    conn.close()
    
    res = "📦 **Бақияи склад:**\n"
    for r in rows: res += f"• {r[0]}: {r[1]} адад\n"
    bot.send_message(message.chat.id, res if rows else "Склад холӣ аст.")

if __name__ == "__main__":
    init_db()
    Thread(target=run).start()
    bot.polling(none_stop=True)
