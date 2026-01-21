import telebot
import sqlite3
import json
from telebot import types
from datetime import datetime

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)

def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Омода кардани база
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)''')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Тугмаи Web App барои фурӯш
    btn_scan = types.KeyboardButton("🚀 СКАНЕРИ ФУРӮШ", web_app=types.WebAppInfo(SCANNER_URL))
    # Тугмаи оддӣ дар бот барои Excel
    btn_excel = types.KeyboardButton("📦 ҚАБУЛИ МОЛ (EXCEL)")
    markup.add(btn_scan)
    markup.add(btn_excel)
    bot.send_message(message.chat.id, "Интихоб кунед:", reply_markup=markup)

# 1. ҚАБУЛИ МОЛ АЗ EXCEL (Матни копяшуда)
@bot.message_handler(func=lambda message: message.text == "📦 ҚАБУЛИ МОЛ (EXCEL)")
def excel_import_start(message):
    msg = bot.send_message(message.chat.id, 
        "📊 **Тарзи қабули мол аз Excel:**\n\n"
        "Маълумотро аз Excel копя кунед ва инҷо фиристед.\n"
        "Формат бояд чунин бошад (бо вергул ё аломати | ҷудо кунед):\n"
        "`Штрихкод, Ном, Нархи_харид, Нархи_фурӯш, Миқдор`\n\n"
        "*Мисол:* `123456, Кола 1л, 5, 8, 100`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_excel_text)

def process_excel_text(message):
    if not message.text:
        bot.send_message(message.chat.id, "❌ Лутфан матн фиристед.")
        return

    lines = message.text.split('\n')
    added = 0
    errors = 0
    
    with get_db() as conn:
        for line in lines:
            try:
                # Ҷудо кардан бо вергул ё аломати |
                parts = [p.strip() for p in line.replace('|', ',').split(',')]
                if len(parts) >= 5:
                    code, name, buy, sell, qty = parts[0], parts[1], float(parts[2]), float(parts[3]), int(parts[4])
                    conn.execute("INSERT OR REPLACE INTO products (code, name, buy, sell, qty) VALUES (?, ?, ?, ?, ?)",
                                 (code, name, buy, sell, qty))
                    added += 1
                else:
                    errors += 1
            except:
                errors += 1
        conn.commit()
    
    bot.send_message(message.chat.id, f"✅ Тамом!\n📥 Илова шуд: {added} мол\n❌ Хатогиҳо: {errors}")

# 2. ҚАБУЛИ МАЪЛУМОТ АЗ СКАНЕР (Web App)
@bot.message_handler(content_types=['web_app_data'])
def handle_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        
        # Агар аз сканер барои фурӯш ояд
        if data['action'] == 'sale':
            items = data['items']
            total = 0
            with get_db() as conn:
                for code, info in items.items():
                    summ = info['qty'] * info['price']
                    total += summ
                    conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                                 (info['name'], summ, datetime.now().strftime("%d.%m.%Y %H:%M")))
                    conn.execute("UPDATE products SET qty = qty - ? WHERE code = ?", (info['qty'], code))
                conn.commit()
            bot.send_message(message.chat.id, f"✅ Фурӯш қабул шуд!\n💰 Ҷамъ: {total} смн")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Хатогӣ: {e}")

if __name__ == "__main__":
    bot.polling(none_stop=True)
