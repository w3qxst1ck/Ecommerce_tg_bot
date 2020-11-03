import telebot
import requests
from telebot import types

import config


bot = telebot.TeleBot(config.token)


def create_buttons():
    """ Create "Список товаров👕", "Корзина📋", "Категории👕👖👟" buttons on the panel
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_list = types.KeyboardButton('Список товаров👕')
    cart = types.KeyboardButton('Корзина📋')
    categories = types.KeyboardButton('Категории👕👖👟')
    markup.row(item_list, cart, categories)
    return markup


@bot.message_handler(commands=['start'])
def handle_text(message):
    bot.send_message(message.from_user.id, 'Hi! You are in ecommerce website.', reply_markup=create_buttons())


@bot.message_handler(commands=['login'])
def handle_text(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_list = types.KeyboardButton('Список товаров👕')
    cart = types.KeyboardButton('Корзина📋')
    categories = types.KeyboardButton('Категории👕👖👟')
    markup.row(item_list, cart, categories)
    mess = '<b>Для авторизации вам необходимо отправить данные в следущей форме:</b>\nlogin:\nusername\npassword'
    bot.send_message(message.from_user.id, mess, reply_markup=markup, parse_mode='html')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    # Авторизация
    if message.text[:6] == 'login:':
        try:
            # Получение токена
            data = message.text[7:].split('\n')
            login = data[0]
            password = data[1]
            response = requests.post('http://127.0.0.1:8000/auth/token/login/', data={
                'username': f'{login}',
                'password': f'{password}'
            }).json()
            auth_token = response['auth_token']

            # Запись токена в файл
            f = open(f'auth_token.txt', 'w')
            f.write(auth_token)
            f.close()

            # Сообщение о входе
            mess = f"Выполнен вход под именем {login}"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_list = types.KeyboardButton('Список товаров👕')
            cart = types.KeyboardButton('Корзина📋')
            categories = types.KeyboardButton('Категории👕👖👟')
            markup.row(item_list, cart, categories)
            bot.send_message(message.from_user.id, mess, reply_markup=markup, parse_mode='html')

        except Exception as e:
            bot.send_message(message.from_user.id, f"Неверные данные.")

    # Вывод списка товаров
    if message.text == 'Список товаров👕':
        start_message = '<u>You can choose these products:\n</u>'
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cart = types.KeyboardButton('Корзина📋')
        categories = types.KeyboardButton('Категории👕👖👟')
        markup.row(cart, categories)
        bot.send_message(message.from_user.id, start_message, reply_markup=markup, parse_mode='html')

        # Список товаров
        url = config.url + 'items/'
        response = requests.get(url).json()
        for item in response:
            # Клавиатура для заказа товаров
            markup = types.InlineKeyboardMarkup(row_width=2)
            add_to_cart = types.InlineKeyboardButton('В корзину ✔', callback_data=f"add_{item['id']}")
            remove_from_cart = types.InlineKeyboardButton('Убрать из корзины ❌', callback_data=f"del_{item['id']}")
            markup.add(add_to_cart, remove_from_cart)

            if item['discount_price']:
                mess = f"<b>{item['title']}</b> - {item['discount_price']}$. Old price - {item['price']}$."
            else:
                mess = f"<b>{item['title']}</b> - {item['price']}$."
            bot.send_message(message.from_user.id, mess, reply_markup=markup, parse_mode='html')

    # Корзина
    if message.text == 'Корзина📋':
        url = config.url + 'cart/'

        # Получение токена из файла
        file = open('auth_token.txt')
        auth_token = file.read()

        response = requests.get(url, headers={'Authorization': f'Token {auth_token}'}).json()

        # Получение товаров в корзине
        try:
            mess = 'ITEMS IN YOUR CART:\n'
            for item in response[0]['items']:
                mess += f"{response[0]['items'].index(item)+1}. <b>{item['item']}</b> - {item['quantity']}шт.\n"
            mess += f"======================================" \
                f"\n<b>Order summary:</b> {response[0]['total_order_amount']} $"
        except Exception:
            mess = 'Ваша корзина пуста.'

        markup_in_cart = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item_list = types.KeyboardButton('Список товаров👕')
        cart = types.KeyboardButton('Корзина📋')
        categories = types.KeyboardButton('Категории👕👖👟')
        markup_in_cart.row(item_list, cart, categories)

        bot.send_message(message.from_user.id, mess, reply_markup=markup_in_cart, parse_mode='html')

    if message.text == 'Категории👕👖👟':
        url = config.url + 'categories/'
        response = requests.get(url).json()
        mess = '<b>Categories:</b>\n\n'
        for c in response:
            mess += f"{c['id']}. {c['title']} ({c['items_count']} items)\n"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item_list = types.KeyboardButton('Список товаров👕')
        cart = types.KeyboardButton('Корзина📋')
        categories = types.KeyboardButton('Категории👕👖👟')
        markup.row(item_list, cart, categories)
        bot.send_message(message.from_user.id, mess, reply_markup=markup, parse_mode='html')

    if message.text[:9] == 'категория' or message.text[:9] == 'Категория':
        # Получение товаров одной категории
        try:
            category_id = message.text[-1]
            url = config.url + f"categories/{category_id}/"
            response = requests.get(url).json()
            mess = f"<b>Items in category \"{response['title']}\":</b>\n\n"
        except Exception:
            mess = f"<b>Wrong category number! Choose one from category list.</b>\n"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item_list = types.KeyboardButton('Список товаров👕')
        cart = types.KeyboardButton('Корзина📋')
        categories = types.KeyboardButton('Категории👕👖👟')
        markup.row(item_list, cart, categories)

        bot.send_message(message.from_user.id, mess, reply_markup=markup, parse_mode='html')

        # Отправка товаров для заказа
        try:
            for item in response['category_items']:
                # Клавиатура для заказа товаров
                markup = types.InlineKeyboardMarkup(row_width=2)
                add_to_cart = types.InlineKeyboardButton('В корзину ✔', callback_data=f"add_{item['id']}")
                remove_from_cart = types.InlineKeyboardButton('Убрать из корзины ❌', callback_data=f"del_{item['id']}")
                markup.add(add_to_cart, remove_from_cart)

                if item['discount_price']:
                    mess = f"<b>{item['title']}</b> - {item['discount_price']}$. Old price - {item['price']}$.\n"
                else:
                    mess = f"<b>{item['title']}</b> - {item['price']}$.\n"
                bot.send_message(message.from_user.id, mess, reply_markup=markup, parse_mode='html')
        except Exception:
            pass


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        # Добавление в корзину
        if call.data[:3] == 'add':
            url = config.url + f"cart/{call.data[4:]}/"

            # Получение токена из файла
            file = open('auth_token.txt')
            auth_token = file.read()

            response = requests.post(url, headers={'Authorization': f'Token {auth_token}'})
            bot.send_message(call.message.chat.id, 'Item has been added to the cart ✅')
        # Удаление из корзины
        if call.data[:3] == 'del':
            url = config.url + f"cart/remove/{call.data[4:]}/"

            # Получение токена из файла
            file = open('auth_token.txt')
            auth_token = file.read()

            response = requests.delete(url, headers={'Authorization': f'Token {auth_token}'})
            bot.send_message(call.message.chat.id, 'Item has been removed from the cart ❌')


bot.polling(none_stop=True)

