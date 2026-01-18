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

# 1. БАЗАИ МОЛҲО (Штрих-код: [Ном, Нархи Харид, Нархи Фурӯш])
PRODUCTS = {
    "4820001234567": ["Оби минералӣ", 2.0, 3.5],
    "4820007654321": ["Шоколад Albeni", 4.0, 6.0],
    "123456": ["Нон", 2.5, 3.0]
}

# 2. РӮЙХАТИ ФУРЎШҲОИ ИМРӮЗА
daily_sales = []

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
        types.KeyboardButton("🛒 Сабад"),
        types.KeyboardButton("❓ Кӯмак")
    )
    
    bot.send_message(message.chat.id, f"Хуш омадед! Молро сканер кунед ё ҳисоботро бинед.", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_scanner_data(message):
    code = message.web_app_data.data
    
    if code in PRODUCTS:
        name, buy_price, sell_price = PRODUCTS[code]
        profit = sell_price - buy_price
        
        # Захираи фурӯш дар хотира
        daily_sales.append({
            'name': name,
            'buy': buy_price,
            'sell': sell_price,
            'profit': profit,
            'time': datetime.now().strftime("%H:%M")
        })
        
        text = (f"✅ Мол ёфт шуд: **{name}**\n"
                f"💰 Нарх: {sell_price} сомонӣ\n"
                f"📈 Фоидаи ин мол: {profit} сомонӣ\n\n"
                f"🛒 Фурӯш қайд карда шуд!")
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ Коди {code} дар база нест.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == "📊 Ҳисоботи имрӯза":
        if not daily_sales:
            bot.send_message(message.chat.id, "Имрӯз ҳанӯз фурӯш нашудааст.")
            return
        
        total_sell = sum(item['sell'] for item in daily_sales)
        total_profit = sum(item['profit'] for item in daily_sales)
        count = len(daily_sales)
        
        report = f"📅 **Ҳисоботи фурӯш:**\n\n"
        for i, sale in enumerate(daily_sales, 1):
            report += f"{i}. {sale['name']} - {sale['sell']} сомонӣ ({sale['time']})\n"
        
        report += f"\n🔢 Шумораи фурӯш: {count} адад"
        report += f"\n💵 Умумӣ: **{total_sell} сомонӣ**"
        report += f"\n💎 Фоидаи соф: **{total_profit} сомонӣ**"
        
        bot.send_message(message.chat.id, report, parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
