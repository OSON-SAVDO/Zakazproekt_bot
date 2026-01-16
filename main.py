import telebot
from telebot import types

# 1. ТОКЕН ВА ID-И ХУДРО ИНҶО ГУЗОРЕД
TOKEN = '8589284419:AAFGfNgr8LjyCC40q7nuvAl7Aq-Y2f-JDT0'
MY_ID = 5863448768  # <--- Ҳатман ID-и худро, ки аз @userinfobot гирифтӣ, инҷо навис!

bot = telebot.TeleBot(TOKEN)

# 2. ФАРМОНИ /START
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 Нархнома")
    btn2 = types.KeyboardButton("📝 Фармоиш додан")
    markup.add(btn1, btn2)
    
    welcome_text = (
        f"Салом, {message.from_user.first_name}! 👋\n"
        "Ин боти хизматрасонии Zakazproekt мебошад.\n"
        "Яке аз тугмаҳоро интихоб кунед:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# 3. ҚАБУЛИ ТУГМАҲО
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "💰 Нархнома":
        prices = (
            "📊 **Нархномаи мо:**\n\n"
            "🔹 Ботҳои оддӣ: аз 80 сомонӣ\n"
            "🔹 Ботҳои тиҷоратӣ: аз 300 сомонӣ\n"
            "🔹 Мағозаҳои онлайн: аз 800 сомонӣ\n\n"
            "Барои маълумоти бештар тугмаи 'Фармоиш додан'-ро пахш кунед."
        )
        bot.send_message(message.chat.id, prices, parse_mode="Markdown")
    
    elif message.text == "📝 Фармоиш додан":
        msg = bot.send_message(message.chat.id, "Лутфан, фармоиши худро пурра нависед (масалан: 'Ман бот барои мағоза мехоҳам'):")
        bot.register_next_step_handler(msg, send_to_admin)

# 4. ФУНКСИЯИ ФИРИСТОДАНИ МАЪЛУМОТ БА АДМИН
def send_to_admin(message):
    try:
        user = message.from_user
        first_name = user.first_name if user.first_name else "Ном надорад"
        last_name = user.last_name if user.last_name else ""
        username = f"@{user.username}" if user.username else "Username надорад"
        
        # Сохтани истинод барои тамос
        if user.username:
            contact_link = f"https://t.me/{user.username}"
        else:
            contact_link = "Истинод дастрас нест (username надорад)"

        # Матни хабар барои ту (Админ)
        admin_info = (
            f"🔔 **ФАРМОИШИ НАВ!**\n\n"
            f"👤 **Муштарӣ:** {first_name} {last_name}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"🔗 **Username:** {username}\n"
            f"📱 **Тамос:** [Барои навиштан пахш кунед]({contact_link})\n\n"
            f"📝 **Матни фармоиш:**\n{message.text}"
        )

        # Фиристодан ба ту
        bot.send_message(MY_ID, admin_info, parse_mode="Markdown", disable_web_page_preview=True)
        
        # Ҷавоб ба муштарӣ
        bot.send_message(message.chat.id, "✅ Ташаккур! Фармоиши шумо қабул шуд. Админ ба зудӣ бо шумо тамос мегирад.")

    except Exception as e:
        print(f"Хатогӣ: {e}")
        bot.send_message(message.chat.id, "❌ Хатогӣ ҳангоми фиристодан. Лутфан қайта кӯшиш кунед.")

# 5. БА КОР АНДОХТАН
print("Бот дар сервер фаъол аст...")
bot.polling(none_stop=True)
