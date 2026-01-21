import telebot, sqlite3, json
from telebot import types
from datetime import datetime

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"
bot = telebot.TeleBot(TOKEN)

def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚀 СКАНЕРИ ФУРӮШ", web_app=types.WebAppInfo(SCANNER_URL)))
    markup.add(types.KeyboardButton("📦 ҚАБУЛИ МОЛ (EXCEL)"))
    bot.send_message(message.chat.id, "Интихоб кунед:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📦 ҚАБУЛИ МОЛ (EXCEL)")
def excel_start(message):
    msg = bot.send_message(message.chat.id, "📊 Маълумотро аз Excel копя карда фиристед:\n`Код, Ном, Харид, Фурӯш, Миқдор`")
    bot.register_next_step_handler(msg, process_excel)

def process_excel(message):
    lines = message.text.split('\n')
    added = 0
    with get_db() as conn:
        for line in lines:
            try:
                p = [i.strip() for i in line.replace('|', ',').split(',')]
                if len(p) >= 5:
                    conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?)", (p[0], p[1], float(p[2]), float(p[3]), int(p[4])))
                    added += 1
            except: continue
        conn.commit()
    bot.send_message(message.chat.id, f"✅ Илова шуд: {added} мол")

@bot.message_handler(content_types=['web_app_data'])
def web_data(message):
    data = json.loads(message.web_app_data.data)
    if data['action'] == 'sale':
        report = "💰 **ЧЕКИ ФУРӮШ:**\n"
        total = 0
        with get_db() as conn:
            for code, info in data['items'].items():
                res = conn.execute("SELECT name, sell FROM products WHERE code=?", (code,)).fetchone()
                name = res['name'] if res else info['name']
                price = res['sell'] if res else 10.0
                summ = info['qty'] * price
                total += summ
                report += f"▪️ {name} x{info['qty']} = {summ} смн\n"
                conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?,?,?)", (name, summ, datetime.now().strftime("%H:%M")))
                conn.execute("UPDATE products SET qty = qty - ? WHERE code = ?", (info['qty'], code))
            conn.commit()
        bot.send_message(message.chat.id, f"{report}\n**ҶАМЪ: {total} смн**", parse_mode="Markdown")

bot.polling(none_stop=True)
