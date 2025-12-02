import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading


TOKEN = "7540936261:AAHAtaMMZM81-EyYKJV6lDg84BT0XRiooZ0"
bot = telebot.TeleBot(TOKEN)


REGION_CHANNELS = {
    "Buxoro": [
        "@Buxoro_Texnika_savdosi",
        "@kinobozr"
    ],
    "others": [
        "@kinobozr"
    ]
}

# ❗ Faqat username bo'ladi
UPLOAD_CHANNEL = "safoyev0_0"


MONGO_URL = "mongodb+srv://safootabekyev_db_user:kKjW0vqmvhPbPzk6@cluster0.pniaa23.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client["kinochi_bot"]
collection = db["videos"]


def check_user(user_id, channels):
    for ch in channels:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


def ask_to_subscribe(chat_id, channels):
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        markup.add(types.InlineKeyboardButton(text=ch, url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton("Tekshirish", callback_data="check_subscribe"))
    bot.send_message(chat_id, "Botdan foydalanish uchun kanallarga obuna bo‘ling:", reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Buxoro", callback_data="region_Buxoro"))
    markup.add(types.InlineKeyboardButton("Boshqa viloyat", callback_data="region_others"))
    bot.send_message(message.chat.id, "Qaysi viloyatdan siz?", reply_markup=markup)


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


@bot.callback_query_handler(func=lambda call: call.data == "check_subscribe")
def check_subscribe(call):
    user_id = call.from_user.id
    region_key = USER_REGION.get(user_id, "others")
    channels = REGION_CHANNELS.get(region_key, REGION_CHANNELS["others"])

    if check_user(user_id, channels):
        bot.send_message(call.message.chat.id, "Botdan foydalanishingiz mumkin!")
    else:
        bot.send_message(call.message.chat.id, "Hali ham barcha kanallarga obuna bo‘lmagansiz!")



# ---------------------------------------------------------
# 🔥 KANALDAN AVTO SAQLASH — FAQAT SHU QO‘SHILDI
# ---------------------------------------------------------
@bot.channel_post_handler(content_types=['video'])
def save_from_channel(message):
    # faqat ushbu kanaldan qabul qilinadi
    if message.chat.username != UPLOAD_CHANNEL:
        return

    if not message.caption:
        return

    caption = message.caption.split("\n")

    # Kodni olish
    kod = caption[0].replace("Kod:", "").strip() if caption else None
    kino_nomi = None

    # Kino nomini topish
    for line in caption:
        if "kino nomi" in line.lower():
            kino_nomi = line.split(":", 1)[1].strip()

    if not kod or not kino_nomi:
        return

    # Botga mos format
    new_caption = f"Kod: {kod}\nKino nomi: {kino_nomi}\nBot nomi: @kinobozor_bot"

    collection.insert_one({
        "kod": kod,
        "file_id": message.video.file_id,
        "caption": new_caption
    })

    bot.send_message(message.chat.id, f"🎬 Kod {kod} saqlandi!")



# ---------------------------------------------------------
# 🔥 FOYDALANUVCHI KOD YUBORGANDA QIDIRISH
# ---------------------------------------------------------
@bot.message_handler(func=lambda msg: msg.text.isdigit())
def search_video(message):
    user_id = message.from_user.id
    region_key = USER_REGION.get(user_id, "others")
    channels = REGION_CHANNELS.get(region_key, REGION_CHANNELS["others"])

    if not check_user(user_id, channels):
        ask_to_subscribe(message.chat.id, channels)
        return

    kod = message.text.strip()

    video = collection.find_one({"kod": kod})

    if video:
        bot.send_video(
            message.chat.id,
            video["file_id"],
            caption=video["caption"]
        )
    else:
        bot.send_message(message.chat.id, "❌ Bu kod bo‘yicha video topilmadi!")



app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ishlayapti!", 200

def run_bot():
    bot.polling(non_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)
