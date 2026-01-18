import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time
from datetime import datetime

# ТОКЕНИ ШУМО
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
# СУРОҒАИ ГИТҲАБ ПЕЙДЖСИ ШУМО
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"
# ID-и шумо (барои он ки танҳо шумо мол илова карда тавонед)
ADMIN_ID = 5863448768 # Инро бо ID-и худатон иваз кунед, агар лозим бошад

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# БАЗАИ МОЛҲО ДАР ХОТИРА (Штрих-код: [Ном, Нархи Харид, Нархи Фурӯш])
PRODUCTS = {
    "12345": ["Нон", 2.0, 2.5]
}

# РӮЙХАТИ ФУРЎШҲО
daily_sales = []

# Барои ҳолати иловакунии мол
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
        types.KeyboardButton("❓ Кӯмак")
    )
    bot.send_message(message.chat.id, f"Хуш омадед! Молро сканер кунед ё илова кунед.", reply_markup=markup)

# --- ФУНКСИЯИ ИЛОВАИ МОЛИ НАВ (АДМИНКА) ---
@bot.message_handler(func=lambda message: message.text == "➕ Иловаи мол")
def add_product_start(message):
    bot.send_message(message.chat.id, "Лутфан, штрих-коди молро фиристед ё сканер кунед:")
    user_states[message.chat.id] = {'step': 'wait_code'}

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_code')
def get_code(message):
    user_states[message.chat.id].update({'code': message.text, 'step': 'wait_name'})
    bot.send_message(message.chat.id, "Номи молро нависед:")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_name')
def get_name(message):
    user_states[message.chat.id].update({'name': message.text, 'step': 'wait_buy_price'})
    bot.send_message(message.chat.id, "Нархи харидро нависед (масалан: 5.50):")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_buy_price')
def get_buy(message):
    user_states[message.chat.id].update({'buy': float(message.text), 'step': 'wait_sell_price'})
    bot.send_message(message.chat.id, "Нархи фурӯшро нависед:")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'wait_sell_price')
def get_sell(message):
    data = user_states[message.chat.id]
    sell_price = float(message.text)
    
    # Илова ба базаи PRODUCTS
    PRODUCTS[data['code']] = [data['name'], data['buy'], sell_price]
    
    bot.send_message(message.chat.id, f"✅ Мол бомуваффақият илова шуд!\n📦 {data['name']}\n💰 Фурӯш: {sell_price} сомонӣ")
    user_states[message.chat.id] = {}

# --- СКАНЕР ВА ҲИСОБОТ ---
@bot.message_handler(content_types=['web_app_data'])
def handle_scanner_data(message):
    code = message.web_app_data.data
    if code in PRODUCTS:
        name, buy, sell = PRODUCTS[code]
        daily_sales.append({'name': name, 'buy': buy, 'sell': sell, 'profit': sell-buy, 'time': datetime.now().strftime("%H:%M")})
        bot.send_message(message.chat.id, f"✅ Фурӯхта шуд: {name}\n💰 Нарх: {sell} сомонӣ")
    else:
        bot.send_message(message.chat.id, f"❌ Коди {code} ёфт нашуд. Тугмаи '➕ Иловаи мол'-ро пахш кунед.")

@bot.message_handler(func=lambda message: message.text == "📊 Ҳисоботи имрӯза")
def show_report(message):
    if not daily_sales:
        bot.send_message(message.chat.id, "Имрӯз ҳанӯз фурӯш нашудааст.")
        return
    
    total_sell = sum(s['sell'] for s in daily_sales)
    total_profit = sum(s['profit'] for s in daily_sales)
    
    report = f"📊 **Ҳисобот:**\n"
    report += f"🔢 Шумораи фурӯш: {len(daily_sales)} адад\n"
    report += f"💵 Маблағи умумӣ: {total_sell} сомонӣ\n"
    report += f"💎 Фоидаи соф: {total_profit} сомонӣ"
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
