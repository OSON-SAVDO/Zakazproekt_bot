import telebot
from telebot import types
import sqlite3
from datetime import datetime
from flask import Flask
from threading import Thread

# 1. ТОКЕНИ ХУДРО ИНҶО ГУЗОРЕД
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE' 
bot = telebot.TeleBot(TOKEN)

# 2. СУРОҒАИ GITHUB PAGES-И ШУМО
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

# --- ҚИСМИ KEEP-ALIVE БАРОИ RENDER (WEB SERVICE) ---
app = Flask('')
@app.route('/')
def home():
    return "Бот фаъол аст!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------------------

# Сохтани Базаи маълумот
def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (barcode TEXT PRIMARY KEY, name TEXT, buy_price REAL, sell_price REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT, qty INTEGER, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Менюи асосӣ
def main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    web_app = types.WebAppInfo(SCANNER_URL)
    
    btn_scan = types.KeyboardButton("📸 Сканер ва Фурӯш", web_app=web_app)
    btn_report = types.KeyboardButton("📊 Ҳисоботи имрӯза")
    btn_add = types.KeyboardButton("➕ Иловаи маҳсулот")
    
    markup.add(btn_scan)
    markup.add(btn_report, btn_add)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "Хуш омадед ба боти Мағоза!\nБот дар сервер фаъол аст.", 
        reply_markup=main_markup()
    )

# Қабули маълумот аз Сканер
@bot.message_handler(content_types=['web_app_data'])
def handle_scan(message):
    barcode = message.web_app_data.data.strip()
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, sell_price FROM products WHERE barcode=?", (barcode,))
    product = cursor.fetchone()
    
    if product:
        name, sell = product
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO sales (barcode, qty, date) VALUES (?, ?, ?)", (barcode, 1, today))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ ФУРӮХТА ШУД:\n📦 Мол: {name}\n💰 Нарх: {sell} сомонӣ")
    else:
        bot.send_message(message.chat.id, f"❌ Маҳсулот ёфт нашуд!\nКод: {barcode}\nИлова кунед: /add")
    conn.close()

# Иловаи маҳсулот
@bot.message_handler(func=lambda message: message.text == "➕ Иловаи маҳсулот")
def add_product_start(message):
    msg = bot.send_message(
        message.chat.id, 
        "Маълумотро чунин фиристед:\n`Код, Ном, Нархи_Харид, Нархи_Фурӯш` \n\n"
        "Мисол:\n`12345678, Шампун, 10, 15`", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_add_product)

def process_add_product(message):
    try:
        data = message.text.split(',')
        barcode = data[0].strip()
        name = data[1].strip()
        buy = float(data[2].strip())
        sell = float(data[3].strip())
        
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)", (barcode, name, buy, sell))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Маҳсулот сабт шуд: {name}")
    except:
        bot.send_message(message.chat.id, "⚠️ Хатогӣ дар формат! Бо вергул ҷудо кунед.")

# Ҳисобот
@bot.message_handler(func=lambda message: message.text == "📊 Ҳисоботи имрӯза")
def get_report(message):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    query = '''
        SELECT SUM(p.sell_price), SUM(p.sell_price - p.buy_price)
        FROM sales s
        JOIN products p ON s.barcode = p.barcode
        WHERE s.date = ?
    '''
    cursor.execute(query, (today,))
    result = cursor.fetchone()
    conn.close()
    
    total_sales = result[0] if result[0] else 0
    total_profit = result[1] if result[1] else 0
    
    bot.send_message(
        message.chat.id, 
        f"📊 Ҳисобот ({today}):\n💰 Фурӯш: {total_sales} сомонӣ\n📈 Фоида: {total_profit} сомонӣ"
    )

if __name__ == "__main__":
    keep_alive() # Ин қисм барои Render лозим аст
    print("Бот фаъол шуд...")
    bot.polling(none_stop=True)
