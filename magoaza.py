import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time

# ТОКЕНИ ШУМО
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
# СУРОҒАИ СКАНЕР
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home(): 
    return "Бот фаъол аст!"

def run(): 
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Тоза кардани конфликтҳо
bot.remove_webhook()
time.sleep(1)

# Фармони /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Тугмаи WebApp барои сканер
    web_app = types.WebAppInfo(SCANNER_URL)
    
    btn_scan = types.KeyboardButton("📸 Сканер", web_app=web_app)
    btn_catalog = types.KeyboardButton("📦 Каталог")
    btn_cart = types.KeyboardButton("🛒 Сабад")
    btn_help = types.KeyboardButton("❓ Кӯмак")
    
    markup.add(btn_scan, btn_catalog, btn_cart, btn_help)
    
    bot.send_message(
        message.chat.id, 
        f"Хуш омадед, {message.from_user.first_name}!\nМолро сканер кунед ё аз каталог интихоб намоед.", 
        reply_markup=markup
    )

# Қабули маълумот аз сканер
@bot.message_handler(content_types=['web_app_data'])
def handle_scanner_data(message):
    scanned_code = message.web_app_data.data
    # Дар ин ҷо шумо метавонед базаи маълумотро тафтиш кунед
    bot.send_message(message.chat.id, f"✅ Мол ёфт шуд!\nКод: {scanned_code}\n\nМехоҳед инро ба сабад илова кунед?")

# Функсияҳои дигар
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text == "📦 Каталог":
        bot.send_message(message.chat.id, "Рӯйхати молҳо дар ҳоли омодасозӣ аст...")
    elif message.text == "🛒 Сабад":
        bot.send_message(message.chat.id, "Сабади шумо холӣ аст.")
    elif message.text == "❓ Кӯмак":
        bot.send_message(message.chat.id, "Барои сканер кардани штрих-код тугмаи '📸 Сканер'-ро пахш кунед.")

if __name__ == "__main__":
    keep_alive()
    print("Бот дар Render ба кор даромад...")
    bot.polling(none_stop=True)
