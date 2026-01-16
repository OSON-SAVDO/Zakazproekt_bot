import telebot
from telebot import types

# Танзимот
TOKEN = '8589284419:AAFGfNgr8LjyCC40q7nuvAl7Aq-Y2f-JDT0'
MY_ID = 123456789  # ID-и худро, ки аз @userinfobot гирифтӣ, инҷо гузор
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 Нархнома")
    btn2 = types.KeyboardButton("📝 Фармоиш додан")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Салом! Бот фаъол аст. Яке аз тугмаҳоро пахш кунед:", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "💰 Нархнома":
        bot.send_message(message.chat.id, "Нархи ботҳо: аз 150 сомонӣ.")
    elif message.text == "📝 Фармоиш додан":
        msg = bot.send_message(message.chat.id, "Лутфан, нависед, ки чӣ гуна бот лозим аст?")
        bot.register_next_step_handler(msg, send_order)

def send_order(message):
    bot.send_message(MY_ID, f"🔔 ФАРМОИШИ НАВ!\n👤 Аз: @{message.from_user.username}\n📝 Матн: {message.text}")
    bot.send_message(message.chat.id, "Ташаккур! Фармоиши шумо қабул шуд.")

print("Бот фаъол шуд...")
bot.polling(none_stop=True)
