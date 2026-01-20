import telebot
import sqlite3
import json
from telebot import types
from datetime import datetime

# ТОКЕНИ ХУДРО ИН ҶО МОН
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)

# Функсия барои пайвастшавӣ ба база
def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Эҷоди ҷадвалҳо агар мавҷуд набошанд
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)''')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Тугмаи асосӣ барои кушодани Web App
    btn_scan = types.KeyboardButton("🚀 КУШОДАНИ СКАНЕР", web_app=types.WebAppInfo(SCANNER_URL))
    markup.add(btn_scan)
    bot.send_message(message.chat.id, "Салом! Барои скан кардани мол тугмаи зерро пахш кунед:", reply_markup=markup)

# ИН ҚИСМ ХЕЛЕ МУҲИМ АСТ! Қабули маълумот аз Web App
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        # Гирифтани JSON аз Web App
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)
        
        if data['action'] == 'receive':
            barcode = data['code']
            # Бот акнун ҷавоб медиҳад!
            msg = bot.send_message(
                message.chat.id, 
                f"📦 **Моли нав скан шуд:** `{barcode}`\n\n"
                "Лутфан маълумотро бо ин формат фиристед:\n"
                "`Ном, Нархи_харид, Нархи_фурӯш, Миқдор` \n\n"
                "Мисол: `Макарон, 5, 7, 50`",
                parse_mode="Markdown"
            )
            # Интизори паёми навбатӣ аз корбар барои захира
            bot.register_next_step_handler(msg, lambda m: save_product(m, barcode))
            
        elif data['action'] == 'sale':
            items = data['items']
            total = 0
            with get_db() as conn:
                for code, info in items.items():
                    total += info['qty'] * info['price']
                    conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                                 (info['name'], info['price'] * info['qty'], datetime.now().strftime("%d.%m.%Y %H:%M")))
                conn.commit()
            bot.send_message(message.chat.id, f"✅ Фурӯш анҷом ёфт! Ҷамъ: {total} смн")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Хатогии техникӣ: {e}")

# Функсияи захира дар база
def save_product(message, barcode):
    try:
        text = message.text
        parts = [i.strip() for i in text.split(',')]
        
        if len(parts) < 4:
            bot.send_message(message.chat.id, "⚠️ Хато! Шумо бояд 4 маълумотро фиристед. Аз нав скан кунед.")
            return

        name, buy, sell, qty = parts
        with get_db() as conn:
            conn.execute("INSERT OR REPLACE INTO products (code, name, buy, sell, qty) VALUES (?, ?, ?, ?, ?)",
                         (barcode, name, float(buy), float(sell), int(qty)))
            conn.commit()
        
        bot.send_message(message.chat.id, f"✅ Мол сабт шуд: *{name}*", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Хато дар формат. Мисол: Ном, 10, 15, 100")

if __name__ == "__main__":
    print("Бот кор карда истодааст...")
    bot.polling(none_stop=True)
