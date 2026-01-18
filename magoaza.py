import telebot, sqlite3
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread
from datetime import datetime

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

def get_db():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    return conn

# --- API БАРОИ СКАНЕРИ ФУРӮШ (ИНТЕРФЕЙСИ ЗИНДА) ---
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
            cursor.execute("UPDATE products SET qty=qty-1 WHERE code=?", (code,))
            cursor.execute("INSERT INTO sales (name, sell_price, profit, date) VALUES (?, ?, ?, ?)", 
                           (name, sell, sell-buy, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok', 'name': name, 'price': sell})
        return jsonify({'status': 'out_of_stock'})
    conn.close()
    return jsonify({'status': 'new', 'code': code})

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Ду WebApp бо як силка, вале вазифаҳои гуногун
    web_app_sale = types.WebAppInfo(SCANNER_URL) 
    markup.add(
        types.KeyboardButton("🟢 ФУРӮШ (КАССА)", web_app=web_app_sale),
        types.KeyboardButton("🔵 ҚАБУЛИ МОЛ (ДОБАВИТЬ)", web_app=web_app_sale),
        types.KeyboardButton("📊 Ҳисобот"),
        types.KeyboardButton("📦 Склад")
    )
    bot.send_message(message.chat.id, "Интихоб кунед:", reply_markup=markup)

# --- МАНТИҚИ ҚАБУЛИ МОЛ (ВАҚТЕ КИ ТУГМАИ КӮҲНАИ SEND_DATA КОР МЕКУНАД) ---
@bot.message_handler(content_types=['web_app_data'])
def handle_restock(message):
    code = message.web_app_data.data
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products WHERE code=?", (code,))
    res = cursor.fetchone()
    
    if res:
        name, qty = res
        bot.send_message(message.chat.id, f"📦 Мол: {name}\nДар склад: {qty} адад ҳаст.\nБоз чанд адад омад? (Танҳо рақам нависед)")
        bot.register_next_step_handler(message, lambda m: update_qty(m, code))
    else:
        bot.send_message(message.chat.id, f"🆕 Моли нав бо коди: {code}\nНоми молро нависед:")
        bot.register_next_step_handler(message, lambda m: get_new_name(m, code))
    conn.close()

def update_qty(message, code):
    try:
        add_qty = int(message.text)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET qty = qty + ? WHERE code = ?", (add_qty, code))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Миқдор зиёд карда шуд!")
    except:
        bot.send_message(message.chat.id, "❌ Хато! Танҳо рақам нависед.")

def get_new_name(message, code):
    name = message.text
    bot.send_message(message.chat.id, f"Маълумоти '{name}'-ро нависед:\nХарид Фурӯш Миқдор (Мисол: 10 15 50)")
    bot.register_next_step_handler(message, lambda m: save_new_product(m, code, name))

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
        bot.send_message(message.chat.id, "❌ Хато! Маълумотро дуруст ворид кунед.")

# Функсияҳои Ҳисобот ва Складро дар поён илова кунед...

def run(): app.run(host='0.0.0.0', port=8080)
if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
