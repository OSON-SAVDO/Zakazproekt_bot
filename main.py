import telebot
from telebot import types

# 1. ТОКЕН ВА ID-И ХУДРО ИНҶО ГУЗОРЕД
TOKEN = '8589284419:AAFGfNgr8LjyCC40q7nuvAl7Aq-Y2f-JDT0'
MY_ID = 5863448768  # <--- ID-и худро аз боти @userinfobot гирифта, инҷо гузор!

bot = telebot.TeleBot(TOKEN)

# Истиноди расми ту аз GitHub
PHOTO_URL = "https://raw.githubusercontent.com/OSON-SAVDO/Zakazproekt_bot/main/Screenshot_20260117_074704.jpg"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 Нархнома")
    btn2 = types.KeyboardButton("📝 Фармоиш додан")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}! Барои фармоиш тугмаро пахш кунед:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💰 Нархнома")
def send_price(message):
    # Фиристодани расм аз GitHub ҳангоми пахши тугмаи Нархнома
    caption_text = (
        "📊 **Нархномаи хизматрасониҳои мо:**\n\n"
        "1. Сохтани боти оддӣ — аз 100 сомонӣ\n"
        "2. Боти мағоза — аз 300 сомонӣ\n"
        "3. Дастгирии техникӣ — ройгон\n\n"
        "Барои фармоиш тугмаи '📝 Фармоиш додан'-ро пахш кунед."
    )
    try:
        bot.send_photo(message.chat.id, PHOTO_URL, caption=caption_text, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, "Бубахшед, расми нархнома дастрас нест. Аммо шумо метавонед мустақиман фармоиш диҳед.")

@bot.message_handler(func=lambda message: message.text == "📝 Фармоиш додан")
def ask_order(message):
    msg = bot.send_message(message.chat.id, "Лутфан, нависед, ки чӣ гуна бот лозим аст?")
    bot.register_next_step_handler(msg, ask_phone)

def ask_phone(message):
    user_order = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_phone = types.KeyboardButton("📞 Фиристодани рақам", request_contact=True)
    markup.add(btn_phone)
    
    msg = bot.send_message(message.chat.id, "Барои тамос бо шумо, лутфан тугмаи '📞 Фиристодани рақам'-ро пахш кунед:", reply_markup=markup)
    bot.register_next_step_handler(msg, send_all_to_admin, user_order)

def send_all_to_admin(message, user_order):
    try:
        if message.contact:
            phone = message.contact.phone_number
            user = message.from_user
            first_name = user.first_name
            username = f"@{user.username}" if user.username else "Username надорад"
            
            admin_msg = (
                f"🔔 **ФАРМОИШИ НАВ!**\n\n"
                f"👤 **Муштарӣ:** {first_name}\n"
                f"📞 **Телефон:** `{phone}`\n"
                f"🔗 **Username:** {username}\n"
                f"🆔 **ID:** `{user.id}`\n\n"
                f"📝 **Фармоиш:** {user_order}"
            )
            
            bot.send_message(MY_ID, admin_msg, parse_mode="Markdown")
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("💰 Нархнома", "📝 Фармоиш додан")
            bot.send_message(message.chat.id, "✅ Ташаккур! Фармоиш ва рақами шумо ба админ фиристода шуд. Мо бо шумо тамос мегирем.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Лутфан тугмаи '📞 Фиристодани рақам'-ро пахш кунед.")
            bot.register_next_step_handler(message, send_all_to_admin, user_order)
            
    except Exception as e:
        print(f"Хатогӣ: {e}")

bot.polling(none_stop=True)
