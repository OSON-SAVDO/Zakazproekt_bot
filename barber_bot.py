import telebot
from telebot import types
from flask import Flask
import threading
import os

# --- БАХШИ ВЕБ-СЕРВЕР БАРОИ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Боти Сартарошхона фаъол аст!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    threading.Thread(target=run).start()

# --- ТАНЗИМОТИ БОТ ---
# ДИҚҚАТ: Токени нави боти барберро инҷо гузоред!
TOKEN = '8290136480:AAF5fJMjTFbtSHcqAICBdsOGT_S_fzeD9v8' 
MY_ID = 5863448768 
bot = telebot.TeleBot(TOKEN)

# Луғати маълумот барои вақтҳои банд: { "13:00": user_id }
bookings = {} 

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✂️ Хизматрасониҳо", "📅 Навбат гирифтан")
    markup.add("❌ Бекор кардани навбат")
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}! Барои навбат гирифтан ё бекор кардан тугмаҳоро истифода баред.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📅 Навбат гирифтан")
def check_time(message):
    busy_slots = list(bookings.keys())
    if not busy_slots:
        busy_text = "Ҳоло ҳамаи вақтҳо холианд."
    else:
        busy_text = "⚠️ **Вақтҳои банд:**\n" + "\n".join([f"🔴 {slot}" for slot in busy_slots])
    
    msg = bot.send_message(message.chat.id, f"{busy_text}\n\nЛутфан вақти омаданатонро нависед (масалан: 13:00):")
    bot.register_next_step_handler(msg, process_booking)

def process_booking(message):
    user_time = message.text.strip()
    user_id = message.from_user.id
    
    # Санҷиши вақт: Оё банд аст?
    if user_time in bookings:
        msg = bot.send_message(message.chat.id, f"❌ Бубахшед, соати **{user_time}** аллакай банд аст. Лутфан вақти дигареро нависед:")
        bot.register_next_step_handler(msg, process_booking)
    else:
        # Захира кардани вақт
        bookings[user_time] = user_id
        
        # Хабар ба админ
        admin_msg = (
            f"📅 **НАВБАТИ НАВ!**\n\n"
            f"👤 **Муштарӣ:** {message.from_user.first_name}\n"
            f"⏰ **Вақт:** {user_time}\n"
            f"🆔 **ID:** {user_id}"
        )
        bot.send_message(MY_ID, admin_msg, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Ташаккур! Соати **{user_time}** барои шумо захира шуд.")

@bot.message_handler(func=lambda message: message.text == "❌ Бекор кардани навбат")
def cancel_booking(message):
    user_id = message.from_user.id
    # Ёфтани вақтҳое, ки маҳз ҳамин муштарӣ гирифтааст
    user_slots = [time for time, uid in bookings.items() if uid == user_id]
    
    if not user_slots:
        bot.send_message(message.chat.id, "Шумо ягон навбати фаъол надоред.")
    else:
        markup = types.InlineKeyboardMarkup()
        for slot in user_slots:
            markup.add(types.InlineKeyboardButton(f"Тоза кардани соати {slot}", callback_data=f"del_{slot}"))
        bot.send_message(message.chat.id, "Кадом навбатро бекор кардан мехоҳед?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
def delete_callback(call):
    time_to_delete = call.data.split('_')[1]
    if time_to_delete in bookings:
        del bookings[time_to_delete]
        bot.edit_message_text(f"✅ Навбати соати {time_to_delete} бекор карда шуд. Акнун ин вақт барои дигарон холӣ аст.", call.message.chat.id, call.message.message_id)
        # Огоҳии админ дар бораи холӣ шудани вақт
        bot.send_message(MY_ID, f"🔔 **ОГОҲӢ:** Муштарӣ навбати соати {time_to_delete}-ро бекор кард. Вақт холӣ шуд!")
    else:
        bot.answer_callback_query(call.id, "Ин навбат аллакай тоза шудааст.")

# --- ҶАВОБИ АДМИН БА МУШТАРӢ ---
@bot.message_handler(func=lambda message: message.reply_to_message is not None and message.chat.id == MY_ID)
def reply_to_user(message):
    try:
        reply_text = message.reply_to_message.text
        target_user_id = reply_text.split("ID: ")[1].strip()
        bot.send_message(target_user_id, f"🔔 **Ҷавоби Сартарош:**\n\n{message.text}")
        bot.send_message(MY_ID, "✅ Ҷавоб фиристода шуд.")
    except:
        bot.send_message(MY_ID, "❌ Хатогӣ: ID-и муштарӣ ёфт нашуд.")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
