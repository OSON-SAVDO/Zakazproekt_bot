import telebot
from telebot import types

# Токени боти Daler_barber_bot
TOKEN = '8290136480:AAF5fJMjTFbtSHcqAICBdsOGT_S_fzeD9v8'
bot = telebot.TeleBot(TOKEN)

# ID-и ту барои гирифтани огоҳиномаҳо
MY_ID = 6900346716 

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💇‍♂️ Хизматрасониҳо ва Нарх")
    btn2 = types.KeyboardButton("📅 Навбатгирӣ (Запись)")
    btn3 = types.KeyboardButton("📍 Суроға ва Тамос")
    markup.add(btn1)
    markup.add(btn2, btn3)
    
    bot.send_message(
        message.chat.id, 
        f"Салом {message.from_user.first_name}! Хуш омадед ба боти сартарошхона. Яке аз бахшҳоро интихоб кунед:", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "💇‍♂️ Хизматрасониҳо ва Нарх")
def show_services(message):
    text = (
        "✂️ **Нархномаи хизматрасониҳо:**\n\n"
        "🔹 Мӯйсарии мардона — 30 сомонӣ\n"
        "🔹 Ислоҳи риш — 20 сомонӣ\n"
        "🔹 Маҷмӯи пурра — 60 сомонӣ"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📅 Навбатгирӣ (Запись)")
def start_booking(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_phone = types.KeyboardButton("📞 Фиристодани рақам", request_contact=True)
    markup.add(btn_phone)
    
    msg = bot.send_message(message.chat.id, "Лутфан, аввал тугмаи '📞 Фиристодани рақам'-ро пахш кунед:", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_time)

def ask_time(message):
    if message.contact:
        phone = message.contact.phone_number
        msg = bot.send_message(message.chat.id, "Ташаккур! Акнун вақти омаданатонро нависед (масалан: 14:00):")
        bot.register_next_step_handler(msg, final_step, phone)
    else:
        bot.send_message(message.chat.id, "Лутфан тугмаро пахш кунед.")

def final_step(message, phone):
    user_time = message.text
    admin_text = (
        f"🔔 **НАВБАТГИРИИ НАВ!**\n\n"
        f"👤 Муштарӣ: {message.from_user.first_name}\n"
        f"📞 Телефон: `{phone}`\n"
        f"⏰ Вақт: {user_time}"
    )
    bot.send_message(MY_ID, admin_text, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ Шумо бо муваффақият сабт шудед!")

bot.polling(none_stop=True)
