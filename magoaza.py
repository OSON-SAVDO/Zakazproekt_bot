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

# Эҷоди база
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)''')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_sale = types.KeyboardButton("🛒 ФУРӮШ (СКАНЕР)", web_app=types.WebAppInfo(SCANNER_URL))
    btn_receive = types.KeyboardButton("📦 ҚАБУЛ АЗ EXCEL")
    markup.add(btn_sale, btn_receive)
    bot.send_message(message.chat.id, "Интихоб кунед:", reply_markup=markup)

# Коркарди пахши тугмаи "ҚАБУЛ АЗ EXCEL"
@bot.message_handler(func=lambda message: message.text == "📦 ҚАБУЛ АЗ EXCEL")
def ask_for_excel_data(message):
    msg = bot.send_message(message.chat.id, 
        "📊 Рӯйхати молҳоро аз Excel копя карда ин ҷо фиристед.\n\n"
        "**Формати зарурӣ:**\n"
        "`Штрихкод | Ном | Нархи харид | Нархи фурӯш | Миқдор` \n\n"
        "Ҳар як мол дар сатри нав бошад.", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_excel_import)

def process_excel_import(message):
    lines = message.text.split('\n')
    count = 0
    errors = 0
    
    with get_db() as conn:
        for line in lines:
            try:
                # Ҷудо кардани маълумот (ту метавонӣ ҷудокунандаро иваз кунӣ, масалан бо пробел ё вергул)
                parts = [p.strip() for p in line.replace('|', ',').split(',')]
                
                if len(parts) >= 5:
                    code, name, buy, sell, qty = parts[0], parts[1], float(parts[2]), float(parts[3]), int(parts[4])
                    conn.execute("INSERT OR REPLACE INTO products (code, name, buy, sell, qty) VALUES (?, ?, ?, ?, ?)",
                                 (code, name, buy, sell, qty))
                    count += 1
            except:
                errors += 1
        conn.commit()
    
    bot.send_message(message.chat.id, f"✅ Иҷро шуд!\n📥 Бор карда шуд: {count} мол\n❌ Хатогиҳо: {errors}")

# Қабули фурӯш аз Web App (Сканкунӣ)
@bot.message_handler(content_types=['web_app_data'])
def handle_sale_from_app(message):
    data = json.loads(message.web_app_data.data)
    if data['action'] == 'sale':
        items = data['items']
        total = 0
        with get_db() as conn:
            for code, info in items.items():
                total += info['qty'] * info['price']
                conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                             (info['name'], info['price'] * info['qty'], datetime.now().strftime("%d.%m.%Y %H:%M")))
            conn.commit()
        bot.send_message(message.chat.id, f"✅ Фурӯш анҷом ёфт!\n💰 Ҷамъ: {total} смн")

if __name__ == "__main__":
    bot.polling(none_stop=True)
