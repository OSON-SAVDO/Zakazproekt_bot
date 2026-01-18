import telebot, sqlite3, time
from telebot import types
from flask import Flask
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

@app.route('/')
def home(): return "Бот фаъол аст!"

def run(): app.run(host='0.0.0.0', port=8080)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    web_app = types.WebAppInfo(SCANNER_URL)
    markup.add(
        types.KeyboardButton("📸 Сканер (Касса)", web_app=web_app),
        types.KeyboardButton("📊 Ҳисоботи имрӯза"),
        types.KeyboardButton("📦 Склад")
    )
    bot.send_message(message.chat.id, "Хуш омадед! Сканерро пахш кунед, то фурӯшро оғоз кунед.", reply_markup=markup)

# --- ИНТИҚОЛИ МАЪЛУМОТ АЗ СКАНЕР ---
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
            # Ба корбар дар чат паём меравад (ин барои тасдиқ)
            bot.send_message(message.chat.id, f"✅ Фурӯхта шуд: {name} - {sell} сомонӣ")
            
            # Огоҳӣ агар мол кам монад
            if new_qty <= 5:
                bot.send_message(message.chat.id, f"⚠️ Мол кам монд: {name} (Боқӣ: {new_qty})")
        else:
            bot.send_message(message.chat.id, f"⚠️ Дар склад нест: {name}")
    else:
        # Агар мол нав бошад
        bot.send_message(message.chat.id, f"🆕 Моли нав! Код: {code}\nНоми молро нависед:")
        bot.register_next_step_handler(message, lambda m: get_new_name(m, code))
    conn.close()

def get_new_name(message, code):
    name = message.text
    bot.send_message(message.chat.id, f"Барои '{name}' нависед:\nХарид Фурӯш Миқдор\n(Мисол: 10 15 100)")
    bot.register_next_step_handler(message, lambda m: save_new_product(m, code, name))

def save_new_product(message, code, name):
    try:
        buy, sell, qty = map(float, message.text.split())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?)", (code, name, buy, sell, int(qty)))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Мол илова шуд: {name}")
    except:
        bot.send_message(message.chat.id, "❌ Хато дар ворид намудани рақамҳо!")

@bot.message_handler(func=lambda m: m.text == "📊 Ҳисоботи имрӯза")
def report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(sell_price), SUM(profit), COUNT(*) FROM sales WHERE date=?", (today,))
    res = cursor.fetchone()
    conn.close()
    if res[2] > 0:
        bot.send_message(message.chat.id, f"📊 Имрӯз:\n🛍 Фурӯш: {res[2]} адад\n💵 Касса: {res[0]} смн\n💎 Фоида: {res[1]} смн")
    else:
        bot.send_message(message.chat.id, "Фурӯш нест.")

@bot.message_handler(func=lambda m: m.text == "📦 Склад")
def stock(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products")
    rows = cursor.fetchall()
    conn.close()
    res = "📦 Склад:\n" + "\n".join([f"• {r[0]}: {r[1]} дона" for r in rows])
    bot.send_message(message.chat.id, res if rows else "Склад холӣ аст.")

if __name__ == "__main__":
    init_db()
    Thread(target=run).start()
    bot.polling(none_stop=True)
