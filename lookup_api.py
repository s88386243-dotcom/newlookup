import telebot
import requests
from telebot import types

BOT_TOKEN = "8931669383:AAEiPZMhLHTOMXfD0CdNPw0BuAgLLQT9YkU"   # अपना BotFather token डालो
ADMIN_ID = 7166502503                  # तुम्हारा Telegram ID

PHONE_API = "https://anshapi.vercel.app/api/num"
PHONE_KEY = "anshapi"

bot = telebot.TeleBot(BOT_TOKEN)

user_search_count = {}
premium_users = set()
lookup_history = {}

def check_limit(user_id):
    if user_id in premium_users:
        return True
    count = user_search_count.get(user_id, 0)
    if count >= 2:
        return False
    else:
        user_search_count[user_id] = count + 1
        return True

@bot.message_handler(commands=['start'])
def start(message):
    banner = (
        "╭━━━〔 🔍 Phone Lookup Bot 〕━━━╮\n"
        "┃ 📌 Welcome!\n"
        "┃ Free limit: 2 searches\n"
        "┃ Premium Plans: 1 Day ₹20 | 1 Week ₹80\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━╯"
    )
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📱 Phone Lookup", callback_data="phone")
    markup.add(btn1)
    bot.send_message(message.chat.id, banner, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "phone":
        bot.send_message(call.message.chat.id, "🔍 Send me a phone number:")
        bot.register_next_step_handler(call.message, lookup_phone)

def send_premium_message(chat_id, user_id):
    markup = types.InlineKeyboardMarkup()
    btn_paid = types.InlineKeyboardButton("✅ मैंने Pay कर दिया", callback_data=f"paid_{user_id}")
    markup.add(btn_paid)

    bot.send_message(chat_id,
        "⚠️ Free limit खत्म हो गया है!\n\n"
        "🌐 Premium Plans:\n"
        "💰 1 Day → ₹20\n"
        "💰 1 Week → ₹80\n\n"
        "👉 QR code scan करके payment करो और फिर नीचे button दबाओ।\n"
        f"🆔 User ID: {user_id}"
    )
    try:
        with open("qr.png", "rb") as qr:
            bot.send_photo(chat_id, qr, caption="📷 Scan and Pay via UPI", reply_markup=markup)
    except:
        bot.send_message(chat_id, "⚠️ QR code image नहीं मिला।", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def paid_callback(call):
    user_id = int(call.data.split("_")[1])
    bot.send_message(ADMIN_ID, f"💰 User {user_id} ने payment किया है। कृपया verify करें।")

@bot.message_handler(commands=['approve'])
def approve(message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id = int(message.text.split()[1])
            premium_users.add(user_id)
            bot.send_message(user_id, "✅ Admin ने आपका premium activate कर दिया है! अब unlimited searches available हैं।")
            bot.reply_to(message, f"User {user_id} को premium दे दिया गया।")
        except:
            bot.reply_to(message, "⚠️ Command format: /approve <user_id>")
    else:
        bot.reply_to(message, "⚠️ सिर्फ admin approve कर सकता है।")

def lookup_phone(message):
    user_id = message.from_user.id
    if not check_limit(user_id):
        send_premium_message(message.chat.id, user_id)
        return

    num = message.text.strip()
    params = {"key": PHONE_KEY, "number": num}
    try:
        response = requests.get(PHONE_API, params=params, timeout=30)
        data = response.json()

        info = None
        if data.get("status") and "data" in data and "Data" in data["data"]:
            records = data["data"]["Data"]
            if "Main_Records" in records and len(records["Main_Records"]) > 0:
                info = records["Main_Records"][0]
            elif "Alt_Records" in records and len(records["Alt_Records"]) > 0:
                info = records["Alt_Records"][0]

        if info:
            result = (
                f"📱 Phone Lookup Result:\n"
                f"👤 Name: {info.get('name','—')}\n"
                f"👨‍👩‍👦 Father: {info.get('fname','—')}\n"
                f"🏠 Address: {info.get('address','—')}\n"
                f"📞 Mobile: {info.get('mobile','—')}\n"
                f"📞 Alt: {info.get('alt','—')}\n"
                f"🌐 Circle: {info.get('circle','—')}\n"
                f"🆔 ID: {info.get('id','—')}\n"
                f"✉️ Email: {info.get('email','—')}\n"
            )
        else:
            result = f"❌ No phone data found.\n\nRaw API Response:\n{data}"

        bot.send_message(message.chat.id, result)

        if user_id not in lookup_history:
            lookup_history[user_id] = []
        lookup_history[user_id].append({"number": num, "result": result})

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ API Error: {str(e)}")

@bot.message_handler(commands=['history'])
def history(message):
    if message.from_user.id == ADMIN_ID:
        text = "📜 Lookup History:\n\n"
        for uid, records in lookup_history.items():
            text += f"👤 User {uid}:\n"
            for rec in records:
                text += f"🔢 {rec['number']} → {rec['result']}\n\n"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "⚠️ History सिर्फ admin देख सकता है।")

print("🤖 Bot is running...")
bot.polling(non_stop=True, interval=0, timeout=60, long_polling_timeout=60)
