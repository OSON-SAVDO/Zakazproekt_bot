import telebot
from telebot import types
import threading
from flask import Flask

# Сервер барои Render
app = Flask('')
@app.route('/')
def home():
    return "Боти Сартарошхона фаъол аст!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_web).start()

# ТАНҲО ТОКЕНИ БОТИ САРТАРОШХОНА
TOKEN = '8290136480:AAF5fJMjTFbtSHcqAICBdsOGT_S_fzeD9v8'
bot = telebot.TeleBot(TOKEN)
MY_ID = 6900346716 

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💇‍♂️ Хизматрасониҳо", "📅 Навбатгирӣ")
    bot.send_message(message.chat.id, "Салом! Хуш омадед ба @Daler_barber_bot", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💇‍♂️ Хизматрасониҳо")
def services(message):
    bot.send_message(message.chat.id, "✂️ Нархнома:\nМӯйсарӣ - 30 сомонӣ")

bot.polling(none_stop=True)
