import telebot
from telebot import types
from flask import Flask
import threading
import os

# --- БАХШИ ВЕБ-СЕРВЕР (МАҲЗ БАРОИ RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "Бот фаъол аст!"

def run():
    # Render талаб мекунад, ки порт аз система гирифта шавад
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Оғози сервер дар замина (background)
threading.Thread(target=run).start()

# --- ТАНЗИМОТИ БОТ ---
TOKEN = '8290136480:AAF5fJMjTFbtSHcqAICBdsOGT_S_fzeD9v8' 
MY_ID = 5863448768 
bot = telebot.TeleBot(TOKEN)

PHOTO_URL = "https://raw.githubusercontent.com/OSON-SAVDO/Zakazproekt_bot/main/Screenshot_20260117_152616.jpg"

# Базаи маълумоти муваққатӣ
bookings = {} 

# --- МЕНЮИ АСОСӢ ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✂️ Хизматрасониҳо", "📅 Навбат гирифтан")
    markup.add("❌ Бекор кардани навбат")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}! Ба боти сартарошхона хуш омадед.", reply_markup=main_menu())

# --- НАРХНОМА ---
@bot.message_handler(func=lambda message: message.text == "✂️ Хизматрасониҳо")
def show_services(message):
    caption_text = (
        "📊 **Нархномаи мо:**\n\n"
        "💇‍♂️ Сартарошӣ — 30 смн\n"
        "🧔 Ислоҳи риш — 20 смн\n"
        "✨ Сурма ва ороиш — 10 смн"
    )
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("📅 Ҳозир навбат мегирам", callback_data="go_book"))
    try:
        bot.send_photo(message.chat.id, PHOTO_URL, caption=caption_text, parse_mode="Markdown", reply_markup=inline_markup)
    except:
        bot.send_message(message.chat.id, caption_text, parse_mode="Markdown", reply_markup=inline_markup)

@bot.callback_query_handler(func=lambda call: call.data == "go_book")
def callback_book(call):
    bot.answer_callback_query(call.id)
    ask_phone(call.message)

# --- НАВБАТГИРӢ ВА ТЕЛЕФОН ---
@bot.message_handler(func=lambda message: message.text == "📅 Навбат гирифтан")
def ask_phone(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 Фиристодани рақам", request_contact=True))
    msg = bot.send_message(message.chat.id, "Лутфан, рақами телефонатонро фиристед:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_time_slots)

def show_time_slots(message):
    if not message.contact:
        bot.send_message(message.chat.id, "❌ Хатогӣ: Рақам фиристода нашуд.", reply_markup=main_menu())
        return
    phone = message.contact.phone_number
    busy_slots = list(bookings.keys())
    busy_text = "⚠️ **Вақтҳои банд:**\n" + "\n".join([f"🔴 {slot}" for slot in busy_slots]) if busy_slots else "Ҳама вақтҳо холианд."
    msg = bot.send_message(message.chat.id, f"{busy_text}\n\nКадом вақт меоед? (масалан: 14:30):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, final_booking, phone)

def final_booking(message, phone):
    user_time = message.text.strip()
    if user_time in bookings:
        msg = bot.send_message(message.chat.id, "❌ Ин вақт банд аст. Вақти дигар нависед:")
        bot.register_next_step_handler(msg, final_booking, phone)
    else:
        bookings[user_time] = {"id": message.from_user.id, "phone": phone}
        bot.send_message(MY_ID, f"📅 **НАВБАТИ НАВ!**\n👤: {message.from_user.first_name}\n📞: `{phone}`\n⏰: {user_time}")
        bot.send_message(message.chat.id, f"✅ Соати {user_time} захира шуд!", reply_markup=main_menu())

# --- БЕКОР КАРДАН ---
@bot.message_handler(func=lambda message: message.text == "❌ Бекор кардани навбат")
def cancel_booking(message):
    uid = message.from_user.id
    user_slots = [t for t, d in bookings.items() if d["id"] == uid]
    if not user_slots:
        bot.send_message(message.chat.id, "Шумо навбати фаъол надоред.")
    else:
        m = types.InlineKeyboardMarkup()
        for s in user_slots:
            m.add(types.InlineKeyboardButton(f"🗑 Тоза кардани {s}", callback_data=f"u_del_{s}"))
        bot.send_message(message.chat.id, "Кадом вақтро бекор мекунед?", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith('u_del_'))
def u_del_callback(call):
    s = call.data.split('_')[2]
    if s in bookings:
        del bookings[s]
        bot.edit_message_text(f"✅ Навбати соати {s} бекор шуд.", call.message.chat.id, call.message.message_id)
        bot.send_message(MY_ID, f"🔔 Муштарӣ соати {s}-ро бекор кард.")

# --- АДМИН ПАНЕЛ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == MY_ID:
        if not bookings: bot.send_message(MY_ID, "Ҳоло ягон навбат нест.")
        else:
            m = types.InlineKeyboardMarkup()
            for s in bookings.keys(): m.add(types.InlineKeyboardButton(f"❌ Холӣ кардани {s}", callback_data=f"a_del_{s}"))
            bot.send_message(MY_ID, "Навбатҳои банд:", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith('a_del_'))
def a_del_callback(call):
    s = call.data.split('_')[2]
    if s in bookings:
        del bookings[s]
        bot.edit_message_text(f"✅ Вақти {s} холӣ шуд.", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
