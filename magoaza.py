import telebot
from telebot import types
import sqlite3
from flask import Flask
from threading import Thread
import time

# ТОКЕНИ ШУМО
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
# СУРОҒАИ ГИТҲАБ ПЕЙДЖСИ ШУМО (Аз расми 4403.jpg)
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home(): return "Бот фаъол аст!"

def run(): app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Ислоҳи хатогии 409: Пеш аз оғоз пауза мекунем
time.sleep(2) 
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = types.WebAppInfo(SCANNER_URL)
    markup.add(types.KeyboardButton("📸 Кушодани Сканер", web_app=web_app))
    bot.send_message(message.chat.id, "Бот омода аст. Тугмаро пахш кунед:", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_data(message):
    bot.send_message(message.chat.id, f"Код қабул шуд: {message.web_app_data.data}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
