import telebot
from telebot import types

# 1. Танзимоти асосӣ
TOKEN = '8589284419:AAFGfNgr8LjyCC40q7nuvAl7Aq-Y2f-JDT0'
MY_ID = 5863448768  # <--- ИНҶО ID-И ХУДРО ГУЗОР!

bot = telebot.TeleBot(TOKEN)

# 2. Фармони /start ва Менюи асосӣ
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Нархнома", "📂 Намунаи корҳо")
    markup.add("📝 Фармоиш додан", "📞 Алоқа")
    
    welcome_text = (
        f"Салом {message.from_user.first_name}! 👋\n"
        "Хуш омадед ба боти хизматрасонии **Zakazproekt**.\n"
        "Мо барои тиҷорати шумо ботҳои босифат месозем."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# 3. Қабули тугмаҳо
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "💰 Нархнома":
        prices = (
            "📊 **Нархномаи хизматрасониҳо:**\n\n"
            "🔹 Бот-визитка: аз 150 сомонӣ\n"
            "🔹 Бот-мағоза: аз 500 сомонӣ\n"
            "🔹 Автоматизатсия: аз 800 сомонӣ\n\n"
            "Барои фармоиш тугмаи '📝 Фармоиш додан'-ро пахш кунед."
        )
        bot.send_message(message.chat.id, prices, parse_mode="Markdown")

    elif message.text == "📂 Намунаи корҳо":
        # Диққат: work1.jpg-ро ба GitHub бор кун ё номашро иваз кун
        photo_url = "https://raw.githubusercontent.com/OSON-SAVDO/Zakazproekt_bot/main/work1.jpg"
        caption_text = (
            "🚀 **Намунаи кор: Бот-мағоза**\n\n"
            "Ин бот дорои каталог ва сабад мебошад. Муштарӣ метавонад "
            "маҳсулотро интихоб кунад ва фармоиш диҳад."
        )
        try:
            bot.send_photo(message.chat.id, photo_url, caption=caption_text, parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, caption_text)

    elif message.text == "📝 Фармоиш додан":
        msg = bot.send_message(message.chat.id, "Лутфан, нависед, ки чӣ гуна бот лозим аст?")
        bot.register_next_step_handler(msg, ask_phone)

    elif message.text == "📞 Алоқа":
        bot.send_message(message.chat.id, "👨‍💻 Админ: @OSON_SAVDO\n📱 Телефон: +992XXXXXXXXX")

# 4. Раванди фармоиш (Пурсидани рақами телефон)
def ask_phone(message):
    user_order = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_phone = types.KeyboardButton("📞 Фиристодани рақам", request_contact=True)
    markup.add(btn_phone)
    
    msg = bot.send_message(message.chat.id, "Барои тамос, лутфан тугмаи '📞 Фиристодани рақам'-ро пахш кунед:", reply_markup=markup)
    bot.register_next_step_handler(msg, send_all_to_admin, user_order)

# 5. Фиристодани маълумоти пурра ба ту (Админ)
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
            
            # Бозгашт ба меню
            bot.send_message(message.chat.id, "✅ Ташаккур! Фармоиши шумо ба админ расид.")
        else:
            bot.send_message(message.chat.id, "Лутфан тугмаро пахш кунед.")
            bot.register_next_step_handler(message, ask_phone)
    except Exception as e:
        print(f"Error: {e}")

bot.polling(none_stop=True)
