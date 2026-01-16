import telebot
from telebot import types

# 1. ТОКЕН ВА ID-И ХУДРО ИНҶО ГУЗОРЕД
TOKEN = '8589284419:AAFGfNgr8LjyCC40q7nuvAl7Aq-Y2f-JDT0'
MY_ID = 123456789  # <--- ID-и худро инҷо гузор!

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 Нархнома")
    btn2 = types.KeyboardButton("📝 Фармоиш додан")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}! Барои фармоиш тугмаро пахш кунед:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📝 Фармоиш додан")
def ask_order(message):
    msg = bot.send_message(message.chat.id, "Лутфан, нависед, ки чӣ гуна бот лозим аст?")
    bot.register_next_step_handler(msg, ask_phone)

def ask_phone(message):
    # Захираи матни фармоиш
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
            
            # Матни пурра барои Админ
            admin_msg = (
                f"🔔 **ФАРМОИШИ НАВ!**\n\n"
                f"👤 **Муштарӣ:** {first_name}\n"
                f"📞 **Телефон:** `{phone}`\n"
                f"🔗 **Username:** {username}\n"
                f"🆔 **ID:** `{user.id}`\n\n"
                f"📝 **Фармоиш:** {user_order}"
            )
            
            bot.send_message(MY_ID, admin_msg, parse_mode="Markdown")
            
            # Бозгашт ба менюи асосӣ
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("💰 Нархнома", "📝 Фармоиш додан")
            bot.send_message(message.chat.id, "✅ Ташаккур! Фармоиш ва рақами шумо ба админ фиристода шуд.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Лутфан тугмаи 'Фиристодани рақам'-ро пахш кунед.")
            bot.register_next_step_handler(message, send_all_to_admin, user_order)
            
    except Exception as e:
        print(f"Хатогӣ: {e}")

bot.polling(none_stop=True)
