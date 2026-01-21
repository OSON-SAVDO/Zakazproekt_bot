import telebot
import sqlite3
import json
from telebot import types
from datetime import datetime

# --- ТАНЗИМОТ ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)

# Функсия барои пайвастшавӣ ба базаи маълумот
def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Эҷоди ҷадвалҳо дар оғози кор
with get_db() as conn:
    # Ҷадвали маҳсулот
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (code TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL, qty INTEGER)''')
    # Ҷадвали фурӯш
    conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, date TEXT)''')

# Фармони /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_scan = types.KeyboardButton("🚀 КУШОДАНИ СКАНЕР", web_app=types.WebAppInfo(SCANNER_URL))
    markup.add(btn_scan)
    bot.send_message(
        message.chat.id, 
        "Хуш омадед! Барои фурӯши мол ё қабули маҳсулоти нав тугмаи зерро пахш кунед:", 
        reply_markup=markup
    )

# Қабули маълумот аз Web App
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        
        # 1. АГАР РЕЖИМИ ҚАБУЛ БОШАД
        if data.get('action') == 'receive':
            barcode = data.get('code')
            msg = bot.send_message(
                message.chat.id, 
                f"📦 **МОЛИ НАВ СКАН ШУД:** `{barcode}`\n\n"
                "Лутфан маълумоти молро бо ин формат фиристед:\n"
                "`Ном, Нархи_харид, Нархи_фурӯш, Миқдор` \n\n"
                "*Мисол:* Кола 1л, 5, 8, 100",
                parse_mode="Markdown"
            )
            # Интизори паёми корбар барои захира дар база
            bot.register_next_step_handler(msg, lambda m: save_product_to_db(m, barcode))
            
        # 2. АГАР РЕЖИМИ ФУРӮШ БОШАД
        elif data.get('action') == 'sale':
            items = data.get('items', {})
            total_sum = 0
            sale_report = "✅ **ФУРӮШИ МУВАФФАҚ:**\n\n"
            
            with get_db() as conn:
                for code, info in items.items():
                    # Санҷиши мавҷудияти мол дар база
                    res = conn.execute("SELECT name, sell FROM products WHERE code=?", (code,)).fetchone()
                    
                    name = res['name'] if res else info['name']
                    price = res['sell'] if res else info['price']
                    qty = info['qty']
                    item_total = price * qty
                    total_sum += item_total
                    
                    sale_report += f"▪️ {name}: {qty} адад = {item_total:.2f} смн\n"
                    
                    # Сабти фурӯш
                    conn.execute("INSERT INTO sales (name, sell_price, date) VALUES (?, ?, ?)", 
                                 (name, item_total, datetime.now().strftime("%d.%m.%Y %H:%M")))
                    
                    # Кам кардани миқдор аз склад (агар мол дар база бошад)
                    conn.execute("UPDATE products SET qty = qty - ? WHERE code = ?", (qty, code))
                
                conn.commit()
            
            sale_report += f"\n💰 **ҶАМЪ: {total_sum:.2f} смн**"
            bot.send_message(message.chat.id, sale_report, parse_mode="Markdown")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Хатогӣ дар коркарди маълумот: {e}")

# Функсияи захира кардани маҳсулот дар база
def save_product_to_db(message, barcode):
    try:
        # Ҷудо кардани маълумот аз матн (бо вергул)
        parts = [i.strip() for i in message.text.split(',')]
        
        if len(parts) < 4:
            bot.send_message(message.chat.id, "⚠️ Хато! Шумо бояд 4 маълумотро нависед. Лутфан аз нав скан кунед.")
            return

        name = parts[0]
        buy_price = float(parts[1])
        sell_price = float(parts[2])
        quantity = int(parts[3])
        
        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO products (code, name, buy, sell, qty) VALUES (?, ?, ?, ?, ?)",
                (barcode, name, buy_price, sell_price, quantity)
            )
            conn.commit()
            
        bot.send_message(
            message.chat.id, 
            f"✅ **МАҲСУЛОТ ЗАХИРА ШУД!**\n\n"
            f"🛒 Ном: {name}\n"
            f"💰 Нархи фурӯш: {sell_price} смн\n"
            f"📦 Дар склад: {quantity} адад",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Хатогӣ ҳангоми захира: {e}\nМисол: `Макарон, 5, 7, 50`")

if __name__ == "__main__":
    print("Бот фаъол аст...")
    bot.polling(none_stop=True)
