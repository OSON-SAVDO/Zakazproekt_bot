import telebot
from telebot import types
from flask import Flask
import threading
import os

# --- БАХШИ ВЕБ-СЕРВЕР ---
app = Flask('')
@app.route('/')
def home(): return "Barber Bot Live!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    threading.Thread(target=run).start()

# --- ТАНЗИМОТИ БОТ ---
TOKEN = '8290136480:AAF5fJMjTFbtSHcqAICBdsOGT_S_fzeD9v8' 
MY_ID = 5863448768 
bot = telebot.TeleBot(TOKEN)

bookings = {} 

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✂️ Хизматрасониҳо", "📅 Навбат гирифтан")
    markup.add("❌ Бекор кардани навбат")
    bot.send_message(message.chat.id, f"Салом! Барои навбат гирифтан тугмаро пахш кунед.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📅 Навбат гирифтан")
def ask_phone(message):
    # Аввал аз муштарӣ рақами телефонашро мепурсем
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("📞 Фиристодани рақам", request_contact=True)
    markup.add(button)
    msg = bot.send_message(message.chat.id, "Лутфан, аввал рақами телефонатонро бо тугмаи поён фиристед:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_time_slots)

def show_time_slots(message):
    if not message.contact:
        bot.send_message(message.chat.id, "Лутфан рақами телефонро фиристед. Бе он навбат гирифтан мумкин нест.")
        return

    phone = message.contact.phone_number
    busy_slots = list(bookings.keys())
    
    if not busy_slots:
        busy_text = "Ҳоло ҳамаи вақтҳо холианд."
    else:
        busy_text = "⚠️ **Вақтҳои банд:**\n" + "\n".join([f"🔴 {slot}" for slot in busy_slots])
    
    msg = bot.send_message(message.chat.id, f"{busy_text}\n\nКадом вақт меоед? (масалан: 13:00):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, final_booking, phone)

def final_booking(message, phone):
    user_time = message.text.strip()
    user_id = message.from_user.id
    
    if user_time in bookings:
        msg = bot.send_message(message.chat.id, "❌ Ин вақт банд шуд. Дигар вақт нависед:")
        bot.register_next_step_handler(msg, final_booking, phone)
    else:
        bookings[user_time] = {"id": user_id, "phone": phone}
        
        # Хабар ба админ бо рақами телефон
        admin_msg = (
            f"📅 **НАВБАТИ НАВ!**\n\n"
            f"👤 **Муштарӣ:** {message.from_user.first_name}\n"
            f"📞 **Телефон:** `{phone}`\n"
            f"⏰ **Вақт:** {user_time}\n"
            f"🆔 **ID:** {user_id}"
        )
        bot.send_message(MY_ID, admin_msg, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Ташаккур! Соати {user_time} захира шуд.")

# --- ФАРМОНИ АДМИН БАРОИ ТОЗАКУНИИ ВАҚТ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == MY_ID:
        if not bookings:
            bot.send_message(MY_ID, "Ҳоло ягон вақт банд нест.")
        else:
            markup = types.InlineKeyboardMarkup()
            for slot in bookings.keys():
                markup.add(types.InlineKeyboardButton(f"❌ Холӣ кардани {slot}", callback_data=f"adm_del_{slot}"))
            bot.send_message(MY_ID, "Рӯйхати вақтҳо:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_del_'))
def admin_del(call):
    slot = call.data.split('_')[2]
    if slot in bookings:
        del bookings[slot]
        bot.edit_message_text(f"✅ Вақти соати {slot} ҳозир холӣ шуд.", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
