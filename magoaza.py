import telebot
import sqlite3
import json
from telebot import types
from datetime import datetime

# --- ТАНЗИМОТ ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)

# Пайвастшавӣ ба база
def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Эҷоди ҷадвалҳо
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)''')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Тугма барои кушодани Web App (Сканери нав)
    btn_scan = types.KeyboardButton("🚀 КУШОДАНИ СКАНЕР", web_app=types.WebAppInfo(SCANNER_URL))
    markup.add(btn_scan)
    bot.send_message(message.chat.id, "Салом! Барои фурӯш ё қабули мол тугмаро пахш кунед:", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        
        # 1. РЕЖИМИ ҚАБУЛ
        if data['action'] == 'receive':
            barcode = data['code']
            msg = bot.send_message(
                message.chat.id, 
                f"📦 **Моли нав скан шуд:** `{barcode}`\n\n"
                "Маълумотро фиристед:\n`Ном, Нарх_харид, Нарх_фурӯш, Миқдор`"
            )
            bot.register_next_step_handler(msg, lambda m: save_product(m, barcode))
            
        # 2. РЕЖИМИ ФУРӮШ
        elif data['action'] == 'sale':
            items = data['items'] # Рӯйхати молҳо аз Web App
            total_all = 0
            report_text = "✅ **ФУРӮШИ НАВ:**\n\n"
            
            with get_db() as conn:
                for code, info in items.items():
                    # Кӯшиш мекунем нарх ва номи аслиро аз база ёбем
                    res = conn.execute("SELECT name, sell FROM products WHERE code=?", (code,)).fetchone()
                    
                    name = res['name'] if res else info['name']
                    price = res['sell'] if res else info['price']
                    qty = info['qty']
                    summ = price * qty
                    total_all += summ
                    
                    report_text += f"🔹 {name} | {qty} адад | {summ} смн\n"
                    
                    # Сабти фурӯш дар база
                    conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                                 (name, summ, datetime.now().strftime("%d.%m.%Y %H:%M")))
                    # Кам кардан аз склад
                    conn.execute("UPDATE products SET qty = qty - ? WHERE code = ?", (qty, code))
                
                conn.commit()
            
            report_text += f"\n💰 **ҶАМЪ: {total_all:.2f} смн**"
            bot.send_message(message.chat.id, report_text, parse_mode="Markdown")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Хато дар Python: {e}")

def save_product(message, code):
    try:
        parts = [i.strip() for i in message.text.split(',')]
        name, buy, sell, qty = parts
        with get_db() as conn:
            conn.execute("INSERT OR REPLACE INTO products (code, name, buy, sell, qty) VALUES (?,?,?,?,?)", 
                         (code, name, float(buy), float(sell), int(qty)))
            conn.commit()
        bot.send_message(message.chat.id, f"✅ Мол ба склад илова шуд: *{name}*", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Хато! Формат: `Ном, 5.50, 8.00, 100`")

if __name__ == "__main__":
    print("Бот фаъол аст...")
    bot.polling(none_stop=True)
