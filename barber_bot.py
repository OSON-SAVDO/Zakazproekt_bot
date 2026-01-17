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

# ИСТИНОДИ НАВИ ШУМО ВОРИД ШУД
PHOTO_URL = "https://raw.githubusercontent.com/OSON-SAVDO/Zakazproekt_bot/main/Screenshot_20260117_152616.jpg"

bookings = {} 

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✂️ Хизматрасониҳо", "📅 Навбат гирифтан")
    markup.add("❌ Бекор кардани навбат")
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}! Ба BarberShop хуш омадед.", reply_markup=markup)

# --- БАХШИ НАРХНОМА ---
@bot.message_handler(func=lambda message: message.text == "✂️ Хизматрасониҳо")
def show_services(message):
    caption_text = (
        "📊 **Нархномаи мо:**\n\n"
        "💇‍♂️ Сартарошӣ — 30 смн\n"
        "🧔 Ислоҳи риш — 20 смн\n"
        "✨ Ороиши шах Бо маслихат- смн\n\n"
        "Барои навбат гирифтан тугмаи поёнро пахш кунед."
    )
    inline_markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📅 Ҳозир навбат мегирам", callback_data="go_book")
    inline_markup.add(btn)
    
    try:
        # Истифодаи расми нав
        bot.send_photo(message.chat.id, PHOTO_URL, caption=caption_text, parse_mode="Markdown", reply_markup=inline_markup)
    except:
        bot.send_message(message.chat.id, caption_text, parse_mode="Markdown", reply_markup=inline_markup)

@bot.callback_query_handler(func=lambda call: call.data == "go_book")
def callback_book(call):
    bot.answer_callback_query(call.id)
    ask_phone(call.message)

# --- РАВАНДИ НАВБАТГИРӢ ---
@bot.message_handler(func=lambda message: message.text == "📅 Навбат гирифтан")
def ask_phone(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("📞 Фиристодани рақам", request_contact=True)
    markup.add(button)
    msg = bot.send_message(message.chat.id, "Лутфан, рақами телефонатонро бо тугмаи поён фиристед:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_time_slots)

def show_time_slots(message):
    if not message.contact:
        bot.send_message(message.chat.id, "❌ Хатогӣ: Лутфан тугмаи '📞 Фиристодани рақам'-ро пахш кунед.")
        return

    phone = message.contact.phone_number
    busy_slots = list(bookings.keys())
    
    busy_text = "⚠️ **Вақтҳои банд:**\n" + "\n".join([f"🔴 {slot}" for slot in busy_slots]) if busy_slots else "Ҳоло ҳамаи вақтҳо холианд."
    
    msg = bot.send_message(message.chat.id, f"{busy_text}\n\nКадом вақт меоед? (масалан: 13:00):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, final_booking, phone)

def final_booking(message, phone):
    user_time = message.text.strip()
    user_id = message.from_user.id
    
    if user_time in bookings:
        msg = bot.send_message(message.chat.id, "❌ Ин вақт банд аст. Дигар вақт нависед:")
        bot.register_next_step_handler(msg, final_booking, phone)
    else:
        bookings[user_time] = {"id": user_id, "phone": phone}
        # Рақами телефон ба админ меравад
        bot.send_message(MY_ID, f"📅 **НАВБАТИ НАВ!**\n👤: {message.from_user.first_name}\n📞: `{phone}`\n⏰: {user_time}\n🆔: {user_id}", parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Соати {user_time} захира шуд!")

# --- БЕКОР КАРДАН ВА АДМИН ---
@bot.message_handler(func=lambda message: message.text == "❌ Бекор кардани навбат")
def cancel_booking(message):
    user_id = message.from_user.id
    user_slots = [time for time, data in bookings.items() if data["id"] == user_id]
    
    if not user_slots:
        bot.send_message(message.chat.id, "Шумо навбати фаъол надоред.")
    else:
        markup = types.InlineKeyboardMarkup()
        for slot in user_slots:
            markup.add(types.InlineKeyboardButton(f"Тоза кардани {slot}", callback_data=f"del_{slot}"))
        bot.send_message(message.chat.id, "Кадом навбатро бекор мекунед?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
def delete_callback(call):
    slot = call.data.split('_')[1]
    if slot in bookings:
        del bookings[slot]
        bot.edit_message_text(f"✅ Навбати соати {slot} бекор шуд.", call.message.chat.id, call.message.message_id)
        bot.send_message(MY_ID, f"🔔 Муштарӣ соати {slot}-ро холӣ кард.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == MY_ID:
        if not bookings: bot.send_message(MY_ID, "Вақтҳо холианд.")
        else:
            markup = types.InlineKeyboardMarkup()
            for slot in bookings.keys(): markup.add(types.InlineKeyboardButton(f"❌ Холӣ кардани {slot}", callback_data=f"adm_del_{slot}"))
            bot.send_message(MY_ID, "Рӯйхати навбатҳо:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_del_'))
def admin_del(call):
    slot = call.data.split('_')[2]
    if slot in bookings:
        del bookings[slot]
        bot.edit_message_text(f"✅ Соати {slot} холӣ шуд.", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
