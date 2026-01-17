import telebot
from telebot import types
from flask import Flask
import threading
import os

# --- БАХШИ FLASK БАРОИ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Бот фаъол аст!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# --- ТАНЗИМОТИ БОТ ---
TOKEN = '8589284419:AAFGfNgr8LjyCC40q7nuvAl7Aq-Y2f-JDT0'
MY_ID = 5863448768 

bot = telebot.TeleBot(TOKEN)
PHOTO_URL = "https://raw.githubusercontent.com/OSON-SAVDO/Zakazproekt_bot/main/Screenshot_20260117_074704.jpg"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Нархнома", "📝 Фармоиш додан")
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}! Барои фармоиш тугмаро пахш кунед:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💰 Нархнома")
def send_price(message):
    caption_text = "📊 **Нархнома:**\n1. Бот - аз 100 смн\n2. Мағоза - аз 300 смн"
    try:
        bot.send_photo(message.chat.id, PHOTO_URL, caption=caption_text, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "Расми нархнома дастрас нест.")

@bot.message_handler(func=lambda message: message.text == "📝 Фармоиш додан")
def ask_order(message):
    msg = bot.send_message(message.chat.id, "Чӣ гуна бот лозим аст?")
    bot.register_next_step_handler(msg, ask_phone)

def ask_phone(message):
    user_order = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 Фиристодани рақам", request_contact=True))
    msg = bot.send_message(message.chat.id, "Рақаматонро фиристед:", reply_markup=markup)
    bot.register_next_step_handler(msg, send_all_to_admin, user_order)

def send_all_to_admin(message, user_order):
    if message.contact:
        phone = message.contact.phone_number
        user = message.from_user
        admin_msg = (
            f"🔔 **ФАРМОИШИ НАВ!**\n\n"
            f"👤 **Муштарӣ:** {user.first_name}\n"
            f"📞 **Телефон:** `{phone}`\n"
            f"🆔 **ID:** {user.id}\n\n"
            f"📝 **Фармоиш:** {user_order}"
        )
        # Бот ба шумо паём мефиристад
        bot.send_message(MY_ID, admin_msg, parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ Фармоиш қабул шуд!")
    else:
        bot.send_message(message.chat.id, "Лутфан тугмаро пахш кунед.")

# --- ФУНКСИЯИ ҶАВОБИ АДМИН ---
@bot.message_handler(func=lambda message: message.reply_to_message is not None and message.chat.id == MY_ID)
def reply_to_user(message):
    try:
        # Гирифтани ID-и муштарӣ аз паёми қаблӣ
        reply_text = message.reply_to_message.text
        target_user_id = reply_text.split("ID: ")[1].split("\n")[0].strip()
        
        bot.send_message(target_user_id, f"🔔 **Ҷавоби админ:**\n\n{message.text}")
        bot.send_message(MY_ID, "✅ Ҷавоб фиристода шуд.")
    except:
        bot.send_message(MY_ID, "❌ Хатогӣ: ID-и муштарӣ ёфт нашуд. Ба паёми фармоиш 'Reply' кунед.")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
