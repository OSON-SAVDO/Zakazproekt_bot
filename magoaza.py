import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time
from datetime import datetime

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# 1. БАЗАИ МОЛҲО (Штрих-код: [Ном, Харид, Фурӯш, Миқдор дар склад])
# Мисол: "123": ["Нон", 2.0, 2.5, 100] -> 100 дона дар склад ҳаст
PRODUCTS = {
    "12345": ["Нон", 2.0, 2.5, 100]
}

# РӮЙХАТИ ФУРЎШҲОИ ИМРӮЗА
daily_sales = []
user_states = {}

@app.route('/')
def home(): return "Бот фаъол аст!"

def run(): app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

bot.remove_webhook()
time.sleep(1)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    web_app = types.WebAppInfo(SCANNER_URL)
    markup.add(
        types.KeyboardButton("📸 Сканер", web_app=web_app),
        types.KeyboardButton("📊 Ҳисоботи имрӯза"),
        types.KeyboardButton("➕ Иловаи мол"),
        types.KeyboardButton("📦 Бақияи молҳо (Склад)")
    )
    bot.send_message(message.chat.id, "Бот омода аст!", reply_markup=markup)

# --- ИЛОВАИ МОЛИ НАВ (Бо миқдор) ---
@bot.message_handler(func=lambda message: message.text == "➕ Иловаи мол")
def add_product_start(message):
    bot.send_message(message.chat.id, "Штрих-кодро нависед ё сканер кунед:")
    user_states[message.chat.id] = {'step': 'wait_code'}

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_code')
def get_code(message):
    user_states[message.chat.id].update({'code': message.text, 'step': 'wait_name'})
    bot.send_message(message.chat.id, "Номи мол:")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_name')
def get_name(message):
    user_states[message.chat.id].update({'name': message.text, 'step': 'wait_buy'})
    bot.send_message(message.chat.id, "Нархи харид:")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_buy')
def get_buy(message):
    user_states[message.chat.id].update({'buy': float(message.text), 'step': 'wait_sell'})
    bot.send_message(message.chat.id, "Нархи фурӯш:")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_sell')
def get_sell(message):
    user_states[message.chat.id].update({'sell': float(message.text), 'step': 'wait_qty'})
    bot.send_message(message.chat.id, "Миқдор (чанд дона ҳаст?):")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_qty')
def get_qty(message):
    data = user_states[message.chat.id]
    qty = int(message.text)
    PRODUCTS[data['code']] = [data['name'], data['buy'], data['sell'], qty]
    bot.send_message(message.chat.id, f"✅ Мол илова шуд: {data['name']}\n📦 Миқдор: {qty} дона")
    user_states[message.chat.id] = {}

# --- СКАНЕР ВА ФУРӮШ ---
@bot.message_handler(content_types=['web_app_data'])
def handle_scanner_data(message):
    code = message.web_app_data.data
    if code in PRODUCTS:
        name, buy, sell, qty = PRODUCTS[code]
        if qty > 0:
            PRODUCTS[code][3] -= 1  # Кам кардан аз склад
            new_qty = PRODUCTS[code][3]
            daily_sales.append({'name': name, 'profit': sell-buy})
            bot.send_message(message.chat.id, f"✅ Фурӯхта шуд: {name}\n💰 Нарх: {sell}\n📦 Боқӣ дар склад: {new_qty} адад")
        else:
            bot.send_message(message.chat.id, f"⚠️ Мол дар склад тамом шуд: {name}")
    else:
        bot.send_message(message.chat.id, f"❌ Коди {code} ёфт нашуд.")

# --- ҲИСОБОТҲО ---
@bot.message_handler(func=lambda message: True)
def reports(message):
    if message.text == "📊 Ҳисоботи имрӯза":
        total_profit = sum(s['profit'] for s in daily_sales)
        bot.send_message(message.chat.id, f"📈 Фоидаи имрӯза: {total_profit} сомонӣ\n🛍 Шумораи фурӯш: {len(daily_sales)} адад")
    
    elif message.text == "📦 Бақияи молҳо (Склад)":
        report = "📦 **Ҳолати склад:**\n"
        for code, info in PRODUCTS.items():
            report += f"• {info[0]}: {info[3]} адад боқӣ монд\n"
        bot.send_message(message.chat.id, report, parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
