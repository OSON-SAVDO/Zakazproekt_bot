import telebot
from telebot import types
from flask import Flask
import threading
import os

# --- БАХШИ ВЕБ-СЕРВЕР (БАРОИ RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "Barber Bot фаъол аст!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# --- ТАНЗИМОТИ БОТ ---
# ТОКЕНИ НАВЕ, КИ БАРОИ БАРБЕР ГИРИФТЕД, ИНҶО ГУЗОРЕД!
TOKEN = 'ТОКЕНИ_НАВИ_ШУМО' 
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    # Тугмаҳои асосии поёнӣ
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✂️ Хизматрасониҳо", "📅 Навбат гирифтан")
    
    welcome_text = f"Салом {message.from_user.first_name}! Хуш омадед ба BarberShop. Кадом хизматрасониро мехоҳед?"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "✂️ Хизматрасониҳо")
def services(message):
    # Тугмаҳои Inline (дар зери паём)
    inline_markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("💇‍♂️ Сартарошӣ - 30 смн", callback_data="cut")
    btn2 = types.InlineKeyboardButton("🧔 Ислоҳи риш - 20 смн", callback_data="beard")
    inline_markup.add(btn1)
    inline_markup.add(btn2)
    
    bot.send_message(message.chat.id, "Рӯйхати хизматрасониҳои мо:", reply_markup=inline_markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cut":
        bot.answer_callback_query(call.id, "Шумо Сартароширо интихоб кардед")
        bot.send_message(call.message.chat.id, "Барои навбат гирифтан '📅 Навбат гирифтан'-ро пахш кунед.")
    elif call.data == "beard":
        bot.answer_callback_query(call.id, "Шумо Ислоҳи ришро интихоб кардед")
        bot.send_message(call.message.chat.id, "Барои навбат гирифтан '📅 Навбат гирифтан'-ро пахш кунед.")

@bot.message_handler(func=lambda message: message.text == "📅 Навбат гирифтан")
def book(message):
    msg = bot.send_message(message.chat.id, "Лутфан вақт ва рӯзи омаданатонро нависед (масалан: Душанбе, 14:00):")
    bot.register_next_step_handler(msg, save_booking)

def save_booking(message):
    user_time = message.text
    bot.send_message(message.chat.id, f"✅ Ташаккур! Мо шуморо соати {user_time} интизор мешавем.")
    # Инҷо метавонед кодро илова кунед, ки ба админ хабар диҳад

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
