import telebot
from telebot import types
import threading
from flask import Flask
import os

# 1. Танзими Flask барои Render
app = Flask('')

@app.route('/')
def home():
    return "Боти Сартарошхона фаъол аст!"

def run_web():
    # Render одатан порти 10000-ро истифода мебарад
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Оғози сервер дар риштаи алоҳида (Thread)
threading.Thread(target=run_web).start()

# 2. Танзими Бот
TOKEN = '8290136480:AAF5fJMjTFbtSHcqAICBdsOGT_S_fzeD9v8'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💇‍♂️ Хизматрасониҳо", "📅 Навбатгирӣ")
    bot.send_message(message.chat.id, "Салом! Хуш омадед ба @Daler_barber_bot", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💇‍♂️ Хизматрасониҳо")
def services(message):
    bot.send_message(message.chat.id, "✂️ Нархнома:\nМӯйсарӣ - 30 сомонӣ")

# 3. Ба кор андохтани бот
if __name__ == "__main__":
    print("Бот кор карда истодааст...")
    bot.polling(none_stop=True)
