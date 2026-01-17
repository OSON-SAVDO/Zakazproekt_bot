import telebot
from telebot import types
import threading
from flask import Flask

# 1. Қисми сервер барои Render (порт 8080)
app = Flask('')

@app.route('/')
def home():
    return "Бот кор карда истодааст!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# Ба кор андохтани сервер дар замина
threading.Thread(target=run_web).start()

# 2. Коди боти ту
TOKEN = '8290136480:AAF5fJMjTFbtSHcqAICBdsOGT_S_fzeD9v8'
bot = telebot.TeleBot(TOKEN)
MY_ID = 6900346716 

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💇‍♂️ Хизматрасониҳо ва Нарх")
    btn2 = types.KeyboardButton("📅 Навбатгирӣ (Запись)")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Салом! Хуш омадед ба боти сартарошхона.", reply_markup=markup)

# Бахши хизматрасониҳо
@bot.message_handler(func=lambda message: message.text == "💇‍♂️ Хизматрасониҳо ва Нарх")
def services(message):
    bot.send_message(message.chat.id, "✂️ Нархнома:\nМӯйсарӣ - 30 сомонӣ\nРиш - 20 сомонӣ")

# Бахши навбатгирӣ
@bot.message_handler(func=lambda message: message.text == "📅 Навбатгирӣ (Запись)")
def booking(message):
    msg = bot.send_message(message.chat.id, "Ном ва вақти омаданатонро нависед:")
    bot.register_next_step_handler(msg, save_data)

def save_data(message):
    bot.send_message(MY_ID, f"🔔 Навбат: {message.text} аз {message.from_user.first_name}")
    bot.send_message(message.chat.id, "✅ Шумо сабт шудед!")

# Оғози бот
bot.polling(none_stop=True)
