import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading

# -----------------------------
#  BOT TOKEN
# -----------------------------
TOKEN = "7540936261:AAHAtaMMZM81-EyYKJV6lDg84BT0XRiooZ0"
bot = telebot.TeleBot(TOKEN)

# -----------------------------
#  KANALLAR (FAQAT BUXORO VA OTHERS)
# -----------------------------
REGION_CHANNELS = {
    "Buxoro": [
        "@Buxoro_Texnika_savdosi",
        "@kinobozr"
    ],
    "others": [
        "@kinobozr"
    ]
}

UPLOAD_CHANNEL = "safoyev0_0"

# -----------------------------
#  MONGO
# -----------------------------
MONGO_URL = "mongodb+srv://safootabekyev_db_user:kKjW0vqmvhPbPzk6@cluster0.pniaa23.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client["kinochi_bot"]
collection = db["videos"]

# -----------------------------
#  OBUNA TEKSHIRISH
# -----------------------------
def check_user(user_id, channels):
    for ch in channels:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# -----------------------------
#  OBUNA SO‘RASH
# -----------------------------
def ask_to_subscribe(chat_id, channels):
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        markup.add(types.InlineKeyboardButton(text=ch, url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton("Tekshirish", callback_data="check_subscribe"))
    bot.send_message(chat_id, "Botdan foydalanish uchun kanallarga obuna bo‘ling:", reply_markup=markup)

# -----------------------------
#  /start — VILOYAT TANLASH
# -----------------------------
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Buxoro", callback_data="region_Buxoro"))
    markup.add(types.InlineKeyboardButton("Boshqa viloyat", callback_data="region_others"))
    bot.send_message(message.chat.id, "Qaysi viloyatdan siz?", reply_markup=markup)

# -----------------------------
#  VILOYAT TANLASH CALLBACK
# -----------------------------
USER_REGION = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("region_"))
def region_select(call):
    user_id = call.from_user.id
    region_key = call.data.replace("region_", "")

    USER_REGION[user_id] = region_key

    bot.answer_callback_query(call.id, f"{region_key} tanlandi!")

    channels = REGION_CHANNELS.get(region_key, REGION_CHANNELS["others"])

    if check_user(user_id, channels):
        bot.send_message(call.message.chat.id, "Siz botdan foydalanishingiz mumkin❗️")
    else:
        ask_to_subscribe(call.message.chat.id, channels)

# -----------------------------
#  TEKSHIRISH TUGMASI
# -----------------------------
@bot.callback_query_handler(func=lambda call: call.data == "check_subscribe")
def check_subscribe(call):
    user_id = call.from_user.id
    region_key = USER_REGION.get(user_id, "others")
    channels = REGION_CHANNELS.get(region_key, REGION_CHANNELS["others"])

    if check_user(user_id, channels):
        bot.send_message(call.message.chat.id, "Botdan foydalanishingiz mumkin!")
    else:
        bot.send_message(call.message.chat.id, "Hali ham barcha kanallarga obuna bo‘lmagansiz!")

# -----------------------------
#  VIDEO QIDIRISH
# -----------------------------
@bot.message_handler(func=lambda msg: msg.text.isdigit())
def search_video(message):
    user_id = message.from_user.id
    region_key = USER_REGION.get(user_id, "others")
    channels = REGION_CHANNELS.get(region_key, REGION_CHANNELS["others"])

    if not check_user(user_id, channels):
        ask_to_subscribe(message.chat.id, channels)
        return

    kod = f"Kod: {message.text}"
    video = collection.find_one({"caption": {"$regex": f"^{kod}", "$options": "m"}})

    if video:
        bot.send_video(
            message.chat.id,
            video["file_id"],
            caption=video["caption"]
        )
    else:
        bot.send_message(message.chat.id, "❌ Bu kod bo‘yicha video topilmadi!")

# -----------------------------
# FLASK VA BOT
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ishlayapti!", 200

def run_bot():
    bot.polling(non_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)
