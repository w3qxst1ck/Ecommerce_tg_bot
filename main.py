import urllib

import telebot
import requests
from telebot import types

import config


bot = telebot.TeleBot(config.token)


def create_buttons():
    """ Create "Список товаров👕", "Корзина📋", "Категории👕👖👟", "Поиск🔎" buttons on the panel
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_list = types.KeyboardButton('Список товаров👕')
    cart = types.KeyboardButton('Корзина📋')
    categories = types.KeyboardButton('Категории👕👖👟')
    search = types.KeyboardButton('Поиск🔎')
    markup.row(categories, item_list, cart, search)
    return markup


def create_inline_button(item):
    """ Create inline button under the message (add to cart, delete from cart)
    """
    # Клавиатура для добавления и удаления из корзины
    markup = types.InlineKeyboardMarkup(row_width=2)
    add_to_cart = types.InlineKeyboardButton('В корзину ✔', callback_data=f"add_{item['id']}")
    remove_from_cart = types.InlineKeyboardButton('Убрать из корзины ❌', callback_data=f"del_{item['id']}")
    markup.add(add_to_cart, remove_from_cart)
    return markup


def get_item_list(message, response):
    """ Get item list (all and by categories)
    """
    for item in response:
        # Текст для описания товара под фото
        if item['discount_price']:
            mess = f"<b>{item['title']}</b> - {item['discount_price']}$. Old price - {item['price']}$."
        else:
            mess = f"<b>{item['title']}</b> - {item['price']}$."

        # Отправка фото c описанием под ним
        url = item['image']
        f = open('files/out.jpg', 'wb')
        f.write(urllib.request.urlopen(url).read())
        f.close()

        img = open('files/out.jpg', 'rb')
        bot.send_photo(message.from_user.id, img, caption=mess, parse_mode='html',
                       reply_markup=create_inline_button(item))


@bot.message_handler(commands=['start'])
def handle_text(message):
    """ Hello message and create bottom buttons
    """
    sti = open('files/stickers/hello.tgs', 'rb')
    bot.send_sticker(message.from_user.id, sti)
    bot.send_message(message.from_user.id, 'Hi! You are in ecommerce website.', reply_markup=create_buttons())


@bot.message_handler(commands=['login'])
def handle_text(message):
    """ Instruction for authorization
    """
    mess = '<b>Для авторизации вам необходимо отправить данные в следущей форме:</b>\nlogin:\nusername\npassword'
    bot.send_message(message.from_user.id, mess, reply_markup=create_buttons(), parse_mode='html')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    """ Handling text messages (login, Список товаров👕, Корзина📋, Категории👕👖👟, Категория id, sale items)
    """
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
            f = open(f'files/auth_token.txt', 'w')
            f.write(auth_token)
            f.close()

            # Сообщение о входе
            sti = open('files/stickers/login.tgs', 'rb')
            bot.send_sticker(message.from_user.id, sti)
            mess = f"Выполнен вход под именем {login}"
            bot.send_message(message.from_user.id, mess, reply_markup=create_buttons(), parse_mode='html')

        except Exception as e:
            bot.send_message(message.from_user.id, f"Неверные данные.")

    # Вывод списка товаров
    if message.text == 'Список товаров👕':
        start_message = '<u>You can choose these products:\n</u>'

        bot.send_message(message.from_user.id, start_message, reply_markup=create_buttons(), parse_mode='html')

        # Список товаров
        url = config.url + 'items/'
        response = requests.get(url).json()
        get_item_list(message, response)

    # Корзина
    if message.text == 'Корзина📋':
        url = config.url + 'cart/'

        # Получение токена из файла
        file = open('files/auth_token.txt')
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

        bot.send_message(message.from_user.id, mess, reply_markup=create_buttons(), parse_mode='html')

    # Категории
    if message.text == 'Категории👕👖👟':
        url = config.url + 'items/categories/'
        response = requests.get(url).json()
        mess = '<b>Categories:</b>\n\n'
        for c in response:
            mess += f"{c['id']}. {c['title']} ({c['items_count']} items)\n"

        cat_1 = types.KeyboardButton('Категория 1')
        cat_2 = types.KeyboardButton('Категория 2')
        cat_3 = types.KeyboardButton('Категория 3')
        cat_4 = types.KeyboardButton('Категория 4')
        cat_5 = types.KeyboardButton('Категория 5')
        sale_items = types.KeyboardButton('Скидка🔥')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(cat_1, cat_2, cat_3, cat_4, cat_5, sale_items)

        bot.send_message(message.from_user.id, mess, reply_markup=markup, parse_mode='html')

    # Вывод одной категории
    if message.text[:9] == 'категория' or message.text[:9] == 'Категория':
        # Получение товаров одной категории
        try:
            category_id = message.text[-1]
            url = config.url + f"items/categories/{category_id}/"
            response = requests.get(url).json()

            mess = f"<b>Items in category \"{response['title']}\":</b>\n\n"
            bot.send_message(message.from_user.id, mess, reply_markup=create_buttons(), parse_mode='html')

            get_item_list(message, response['category_items'])
        except Exception:
            mess = f"<b>Wrong category number! Choose one from category list.</b>\n"
            bot.send_message(message.from_user.id, mess, reply_markup=create_buttons(), parse_mode='html')

    # Товары со скидкой
    if message.text == 'Скидка🔥':
        url = config.url + 'items/?discount_price=false'
        response = requests.get(url).json()
        mess = 'SALE ITEMS🔥\n\n'
        bot.send_message(message.from_user.id, mess, reply_markup=create_buttons(), parse_mode='html')
        get_item_list(message, response)

    # Поиск по товарам
    if message.text == 'Поиск🔎':
        mess = '<b>Отправте текст поска в следущей форме:</b>\n' \
               'Поиск: <i>&lt;название товара/ категории/ описание&gt"</i>'
        bot.send_message(message.from_user.id, mess, reply_markup=create_buttons(), parse_mode='html')

    if message.text[:7] == 'Поиск: ':
        search_param = message.text[7:]
        url = config.url + f"items/?search={search_param}"
        response = requests.get(url).json()
        if response:
            get_item_list(message, response)
        else:
            mess = 'По вашему запросу ничего не найдено.'
            bot.send_message(message.from_user.id, mess, reply_markup=create_buttons(), parse_mode='html')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    """ Handling messages from inline keyboard (add to cart, delete from cart)
    """
    if call.message:

        # Добавление в корзину
        if call.data[:3] == 'add':
            url = config.url + f"cart/{call.data[4:]}/"

            # Получение токена из файла
            file = open('files/auth_token.txt')
            auth_token = file.read()

            response = requests.post(url, headers={'Authorization': f'Token {auth_token}'})
            sti = open('files/stickers/add.tgs', 'rb')
            bot.send_sticker(call.message.chat.id, sti)
            bot.send_message(call.message.chat.id, 'Item has been added to the cart ✅')

        # Удаление из корзины
        if call.data[:3] == 'del':
            url = config.url + f"cart/remove/{call.data[4:]}/"

            # Получение токена из файла
            file = open('files/auth_token.txt')
            auth_token = file.read()

            response = requests.delete(url, headers={'Authorization': f'Token {auth_token}'})
            bot.send_message(call.message.chat.id, 'Item has been removed from the cart ❌')


bot.polling(none_stop=True)

