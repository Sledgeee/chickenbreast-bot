import os
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand, User
from utils import api_request
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
bot = TeleBot(BOT_TOKEN, threaded=False)


@bot.message_handler(commands=['start'])
def start_cmd(message: Message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Авторизуватись в адмін-панель", callback_data="login"))
    markup.row(InlineKeyboardButton("Отримати посилання на адмін-панель", callback_data="panel"))
    markup.row(InlineKeyboardButton("Зробити запит на отримання прав адміна", callback_data="get_admin"))
    bot.send_message(message.chat.id, "Привіт, обирай, що потрібно:", reply_markup=markup)


def login(from_user: User):
    try:
        user_id = from_user.id
        is_admin = api_request('post', f'auth/has-rights/{user_id}')['result']
        if is_admin:
            attempt = api_request('post', 'auth/cml', json={
                "userId": user_id,
                "username": from_user.username
            })
            endpoint = "https://panel.chickenbreast.pp.ua/magic-login"
            bot.send_message(user_id, "Для авторизації в панель "
                                      "використайте посилання нижче (воно дійсне протягом 5 хвилин):\n"
                                      f"{endpoint}?uid={attempt['userId']}&un={attempt['username']}"
                                      f"&otp={attempt['otp']}&hash={attempt['_id']}",
                             protect_content=True,
                             disable_web_page_preview=True)
        else:
            bot.send_message(from_user.id, "У вас немає прав адміністратора ❌")
    except:
        pass


@bot.message_handler(commands=["login"])
def login_cmd(message: Message):
    user = message.from_user
    login(user)


def get_admin_account(from_user: User):
    try:
        if api_request('post', f'auth/has-rights/{from_user.id}')['result']:
            bot.send_message(from_user.id, "Ви вже маєте права адміністратора ⚠️")
            return

        if api_request('post', f'auth/has-request/{from_user.id}')['result']:
            bot.send_message(from_user.id, "Ви вже зробили запит на отримання прав адміністратора ⚠️")
            return

        api_request('post', 'auth/create-request', json={
            'userId': from_user.id,
            'username': from_user.username
        })
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Одобрити ✅", callback_data=f"aa_{from_user.id}"),
            InlineKeyboardButton("Відхилити ❌", callback_data=f"da_{from_user.id}")
        )
        bot.send_message(OWNER_ID, f"@{from_user.username} зробив заявку на реєстрацію адмін-аккаунту:",
                         reply_markup=markup)
        bot.send_message(from_user.id,
                         "Запит на реєстрацію створено, очікуйте на відповідь ⏳")
    except:
        pass


def handle_get_admin_account_accepted(user_id):
    try:
        msg = bot.send_message(user_id,
                               "Ваш запит на отримання прав адміністратора схвалено ✅\n"
                               "Придумайте логін для вашого аккаунта, я буду очікувати на вашу відповідь...")
        bot.register_next_step_handler(msg, handle_username_typed)
    except:
        pass


def handle_username_typed(message: Message):
    try:
        username = message.text
        if username.isalnum() and username.isascii():
            response = api_request('post', 'auth/register', json={
                "userId": int(message.chat.id),
                "username": username
            })
            if "message" in response:
                bot.send_message(message.chat.id, 'Цей логін вже існує, спробуйте інший')
                bot.register_next_step_handler(message, handle_username_typed)
            else:
                bot.send_message(message.chat.id, 'Аккаунт успішно створено ✅')
        else:
            bot.send_message(message.chat.id, 'Ви ввели некорректний логін, він може містити тільки англ. літери та цифри.'
                                              'Спробуйте ще раз, я буду очікувати на вашу відповідь...')
            bot.register_next_step_handler(message, handle_username_typed)
    except:
        pass


@bot.message_handler(commands=["register"])
def get_admin_role_cmd(message: Message):
    user = message.from_user
    get_admin_account(user)


def panel(from_user: User):
    bot.send_message(from_user.id, "https://panel.chickenbreast.pp.ua", disable_web_page_preview=True)


@bot.message_handler(commands=["panel"])
def panel_cmd(message: Message):
    user = message.from_user
    panel(user)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: CallbackQuery):
    try:
        if call.data == "login":
            login(call.from_user)
        elif call.data == "panel":
            panel(call.from_user)
        elif call.data == "get_admin":
            get_admin_account(call.from_user)
        elif "aa_" in call.data:
            user_id = int(call.data.split("_")[1])
            handle_get_admin_account_accepted(user_id)
        elif "da_" in call.data:
            user_id = call.data.split("_")[1]
            api_request('delete', f'auth/delete-request/{user_id}')
            bot.send_message(user_id, "Ваш запит на отримання прав адміністратора відхилено ❌")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass


admin_commands = [
    BotCommand("/start", "Розпочати діалог з ботом"),
    BotCommand("/register", "Створити адмін-аккаунт"),
    BotCommand("/panel", "Отримати посилання на панель"),
    BotCommand("/login", "Авторизуватись в панель через магічне посилання")
]
bot.set_my_commands(commands=admin_commands)
