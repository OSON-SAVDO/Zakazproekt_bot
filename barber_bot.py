import telebot
from telebot import types
from flask import Flask
import threading
import os

# --- БАХШИ FLASK БАРОИ RENDER (Ислоҳи шахшавӣ) ---
app = Flask('')

@app.route('/')
def home():
    return "Боти Сартарошхона фаъол аст!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# --- ТАНЗИМОТИ БОТ ---
# ДИҚҚАТ: Инҷо ТОКЕНИ НАВ-и боти барберро гузоред!
TOKEN = 'ИНҶО_ТОКЕНИ_НАВИ_БАРБЕР_РО_ГУЗОРЕД' 
MY_ID = 5863448768 

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✂️ Хизматрасониҳо", "📅 Навбат гирифтан")
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}! Ба BarberShop хуш омадед.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "✂️ Хизматрасониҳо")
def services(message):
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("💇‍♂️ Сартарошӣ - 30 смн", callback_data="cut"))
    inline_markup.add(types.InlineKeyboardButton("🧔 Ислоҳи риш - 20 смн", callback_data="beard"))
    bot.send_message(message.chat.id, "Хизматрасониҳо:", reply_markup=inline_markup)

@bot.message_handler(func=lambda message: message.text == "📅 Навбат гирифтан")
def book(message):
    msg = bot.send_message(message.chat.id, "Лутфан вақти омаданатонро нависед (масалан: 15:00):")
    bot.register_next_step_handler(msg, send_booking_to_admin)

def send_booking_to_admin(message):
    user_time = message.text
    user = message.from_user
    admin_msg = (
        f"📅 **НАВБАТИ НАВ!**\n\n"
        f"👤 **Муштарӣ:** {user.first_name}\n"
        f"🆔 **ID:** {user.id}\n"
        f"⏰ **Вақт:** {user_time}"
    )
    bot.send_message(MY_ID, admin_msg, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ Ташаккур! Админ вақтро тасдиқ мекунад.")

# --- ФУНКСИЯИ ҶАВОБИ АДМИН ---
@bot.message_handler(func=lambda message: message.reply_to_message is not None and message.chat.id == MY_ID)
def reply_to_user(message):
    try:
        reply_text = message.reply_to_message.text
        target_user_id = reply_text.split("ID: ")[1].split("\n")[0].strip()
        bot.send_message(target_user_id, f"🔔 **Ҷавоби Сартарош:**\n\n{message.text}")
        bot.send_message(MY_ID, "✅ Ҷавоб ба муштарӣ фиристода шуд.")
    except:
        bot.send_message(MY_ID, "❌ Хатогӣ: ID ёфт нашуд. Ба паёми навбат 'Reply' кунед.")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
