import telebot
from telebot import types

# 1. ТОКЕН ВА ID-И ХУДРО ИНҶО ГУЗОРЕД
TOKEN = '8589284419:AAFGfNgr8LjyCC40q7nuvAl7Aq-Y2f-JDT0'
MY_ID = 5863448768  # <--- Ҳатман ID-и худро инҷо навис!

bot = telebot.TeleBot(TOKEN)

# 2. ФАРМОНИ /START
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 Нархнома")
    btn2 = types.KeyboardButton("📝 Фармоиш додан")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f"Салом {message.from_user.first_name}! Барои фармоиш туag тугмаро пахш кунед:", reply_markup=markup)

# 3. ҚАБУЛИ ТУГМАҲО
@bot.message_handler(func=lambda message: message.text == "📝 Фармоиш додан")
def ask_order(message):
    msg = bot.send_message(message.chat.id, "Лутфан, нависед, ки чӣ гуна бот лозим аст?")
    bot.register_next_step_handler(msg, ask_phone)

# 4. ПУРСИДАНИ РАҚАМИ ТЕЛЕФОН
def ask_phone(message):
    user_order = message.text # Фармоиши муштариро захира мекунем
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    # Тугмаи махсус барои фиристодани рақам
    btn_phone = types.KeyboardButton("📞 Фиристодани рақам", request_contact=True)
    markup.add(btn_phone)
    
    msg = bot.send_message(message.chat.id, "Барои тамос бо шумо, лутфан тугмаи '📞 Фиристодани рақам'-ро пахш кунед:", reply_markup=markup)
    bot.register_next_step_handler(msg, send_all_to_admin, user_order)

# 5. ФИРИСТОДАНИ МАЪЛУМОТИ ПУРРА БА АДМИН
def send_all_to_admin(message, user_order):
    try:
        if message.contact:
            phone = message.contact.phone_number
            user = message.from_user
            first_name = user.first_name
            username = f"@{user.username}" if user.username else "Username надорад"
            
            # Матни пурра барои ту (Админ)
            admin_msg = (
                f"🔔 **ФАРМОИШИ НАВ!**\n\n"
                f"👤 **Муштарӣ:** {first_name}\n"
                f"📞 **Телефон:** `{phone}`\n"
                f"🔗 **Username:** {username}\n"
                f"🆔 **ID:** `{user.id}`\n\n"
                f"📝 **Фармоиш:** {user_order}"
            )
            
            bot.send_message(MY_ID, admin_msg, parse_mode="Markdown")
            
            # Баргардонидани менюи асосӣ
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("💰 Нархнома", "📝 Фармоиш додан")
            bot.send_message(message.chat.id, "✅ Ташаккур! Фармоиш ва рақами шумо ба админ фиристода шуд. Мо бо шумо тамос мегирем.", reply_markup=markup)
        else:
            # Агар муштарӣ рақам нафиристад, боз мепурсад
            bot.send_message(message.chat.id, "Лутфан, барои идома додани фармоиш тугмаи '📞 Фиристодани рақам'-ро пахш кунед.")
            bot.register_next_step_handler(message, ask_phone)
            
    except Exception as e:
        print(f"Хатогӣ: {e}")

# ТУГМАИ НАРХНОМА
@bot.message_handler(func=lambda message: message.text == "💰 Нархнома")
def show_price(message):
    bot.send_message(message.chat.id, "Нархи бот Хо
    Боти Оди 80 сомон
    бот барои Тичорат 250 сомон
    бот барои Магоза 600 сомон.")

bot.polling(none_stop=True)
