import telebot
from telebot import types
import sqlite3
from datetime import datetime

# ТОКЕНИ БОТИ МАҒОЗА
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'
bot = telebot.TeleBot(TOKEN)

# URL-И СКАНИР
SCANNER_URL = "https://oson-savdo.github.io/Zakazproekt_bot/"

def init_db():
    conn = sqlite3.connect('magaza_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS products (barcode TEXT PRIMARY KEY, name TEXT, buy REAL, sell REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, barcode TEXT, date TEXT)')
    conn.commit()
    conn.close()

init_db()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = types.WebAppInfo(SCANNER_URL)
    markup.add(types.KeyboardButton("📸 Сканер", web_app=web_app))
    markup.add("📊 Ҳисобот", "➕ Иловаи мол")
    bot.send_message(message.chat.id, "Бот-Мағоза фаъол аст!", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_scan(message):
    barcode = message.web_app_data.data
    bot.send_message(message.chat.id, f"Коди сканершуда: {barcode}")

bot.polling(none_stop=True)
