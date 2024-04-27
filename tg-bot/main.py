import telebot
import threading
from telebot import types
import requests
import json
import schedule
import time
import pytz
from config import bot_api, weather_api

bot = telebot.TeleBot(bot_api)
API = weather_api
KGD_TIMEZONE = pytz.timezone('Europe/Kaliningrad')
city = {}
notes = []
user_id = []
user_times = {}

send = bot.send_message


def send_morning_message(chat_id):
    username = bot.get_chat(chat_id).first_name
    send(chat_id, f"Доброе утро, {username}! ☀️")
    get_weather_for_my_lord(chat_id)


@bot.message_handler(commands=['start'])
def welcome(message):
    global user_id
    global city
    city[message.chat.id] = 'zelenogradsk'
    user_id.append(message.chat.id)
    button = types.InlineKeyboardButton('Меню', callback_data='menu')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    send(message.chat.id, '<b>Добро пожаловать!</b>\nЭто бот, который покажет вам погоду, '
                          'а так же сообщит вам утром\nПерейдите в меню, чтобы посмотреть функции',
         parse_mode='HTML', reply_markup=markup)


@bot.message_handler(commands=['instructions'])
def instructions(message):
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    send(message.chat.id, '--------------Инструкция--------------\n'
                          '- Это телеграм бот, который подскажет вам погоду в своём городе\n- Бот хранит в себе '
                          '8 функций'
                          ' для удобного использования\n\n\n------------Список функций------------\n\n- /start '
                          '--'
                          ' команда для запуска бота.\n\n- /weather -- команда для просмотра погоды (по умолчанию стоит'
                          ' '
                          'город Зеленоградск).\n\n- /menu -- команда, позволяющая открыть меню.\n\n- /setcity -- '
                          'команда, '
                          'позволяющая установить другой город.\n\n- /createnote -- команда, позволяющая создать '
                          'заметку.\n\n- '
                          '/shownote -- команда, позволяющая посмотреть все заметки\n\n- /deletenote -- команда, '
                          'позволяющая удалить заметку.\n\n- /settime -- команда, позволяющая установить время отправки'
                          ' сообщения ботом. Если команда не была использована, бот отправлять сообщения не будет.'
                          '\n\n- '
                          '/instructions -- команда, позволяющая открыть инструкцию бота\n\n- кнопки <b>Ок</b>, '
                          '<b>Удалить сообщения</b> позволяют удалять уже ненужные сообщения. Это сделано для того, '
                          'чтобы чат не засорялся.', parse_mode='HTML', reply_markup=markup)


@bot.message_handler(commands=['weather'])
def say_hello(message):
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    bot.delete_message(message.chat.id, message.message_id)
    if message.chat.id in user_id:
        send(message.chat.id, f'Доброго времени суток!')
        show_weather(message)
    else:
        send(message.chat.id, 'Произошел сбой. Нажмите или введите команду /start, и попробуйте еще раз',
             reply_markup=markup)


@bot.message_handler(commands=['setcity'])
def set_city_ask(message):
    bot.delete_message(message.chat.id, message.message_id)
    button_zlk = types.InlineKeyboardButton('Зеленоградск', callback_data='set_city_zlk')
    button_kgd = types.InlineKeyboardButton('Калининград', callback_data='set_city_kgd')
    button_svg = types.InlineKeyboardButton('Светлогорск', callback_data='set_city_svg')
    button_pnr = types.InlineKeyboardButton('Пионерский', callback_data='set_city_pnr')
    button_ynt = types.InlineKeyboardButton('Янтарный', callback_data='set_city_ynt')
    button_blsk = types.InlineKeyboardButton('Балтийск', callback_data='set_city_blsk')
    button_ldn = types.InlineKeyboardButton('Ладушкин', callback_data='set_city_ldn')
    button_mmn = types.InlineKeyboardButton('Мамоново', callback_data='set_city_mmn')
    button_svsk = types.InlineKeyboardButton('Советск', callback_data='set_city_svsk')
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(button_zlk, button_kgd, button_svg, button_pnr, button_ynt, button_blsk, button_ldn, button_mmn,
               button_svsk)
    send(message.chat.id, 'Выберите ваш город:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_note_'))
def callback_delete_note(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    note_num_to_delete = int(call.data.split('_')[-1])
    for note in reversed(notes):
        if note[0] == note_num_to_delete and note[2] == call.message.chat.id:
            notes.remove(note)
            break
    bot.send_message(call.message.chat.id, f"Заметка №{note_num_to_delete} удалена!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    button_menu = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    button_weather = types.InlineKeyboardButton('Узнать погоду', callback_data='get_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button_menu, button_weather)
    global city
    if call.data == 'menu':
        menu(call.message)
    if call.data == 'get_weather':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_weather(call.message)

    elif call.data == 'clear_weather':
        clear_weather(call.message)

    elif call.data == 'set_city_zlk':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'zelenogradsk'
        send(call.message.chat.id, 'Город Зеленоградск установлен!', reply_markup=markup)

    elif call.data == 'set_city_kgd':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'kaliningrad'
        send(call.message.chat.id, 'Город Калининград установлен!', reply_markup=markup)

    elif call.data == 'set_city_svg':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'svetlogorsk'
        send(call.message.chat.id, 'Город Свтелогорск установлен!', reply_markup=markup)

    elif call.data == 'set_city_pnr':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'pionerskiy'
        send(call.message.chat.id, 'Город Пионерский установлен!', reply_markup=markup)

    elif call.data == 'set_city_ynt':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'yantarnyy'
        send(call.message.chat.id, 'Город Янтарный установлен!', reply_markup=markup)

    elif call.data == 'set_city_blsk':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'baltiysk'
        send(call.message.chat.id, 'Город Балтийск установлен!', reply_markup=markup)

    elif call.data == 'set_city_ldn':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'ladushkin'
        send(call.message.chat.id, 'Город Ладушкин установлен!', reply_markup=markup)

    elif call.data == 'set_city_mmn':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'mamonovo'
        send(call.message.chat.id, 'Город Мамоново установлен!', reply_markup=markup)

    elif call.data == 'set_city_svsk':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        city[call.message.chat.id] = 'sovetsk'
        send(call.message.chat.id, 'Город Советск установлен!', reply_markup=markup)


@bot.message_handler(commands=['menu'])
def menu(message):
    button = types.InlineKeyboardButton('Закрыть меню', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    bot.delete_message(message.chat.id, message.message_id)
    send(message.chat.id, '<b>----------------Меню----------------</b>\n\n/weather -- показать погоду'
                          '\n-------------------------------------\n/menu -- меню (вы находитесть в меню)'
                          '\n-------------------------------------\n/setcity -- установить другой город'
                          '\n-------------------------------------\n/createnote -- создать заметку'
                          '\n-------------------------------------\n/shownotes -- Посмотреть мои заметки'
                          '\n-------------------------------------\n/deletenote -- удалить заметку'
                          '\n-------------------------------------\n/settime -- установить время отправки ботом '
                          'сообщения'
                          '\n-------------------------------------\n/instructions -- инструкция  по использованию бота'
                          '\n'
                          '\n-------------------------------------\nНажмите на любую из команд, которая вам нужна',
         parse_mode='HTML', reply_markup=markup)


def get_weather_for_my_lord(chat_id):
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(button)

    try:
        user_city = city.get(chat_id)
    except Exception:
        user_city = 'zelenogradsk'
    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={user_city}&appid={API}&units=metric')
    data = json.loads(res.text)
    weather_data = data['weather'][0]

    text = (f'Погода в {user_city}:'
            f'\n-------------------------------\nТемпература: <b>{data["main"]["temp"]}°</b>'
            f'\n-------------------------------\nОщущается как: <b>{data["main"]["feels_like"]}°</b>'
            f'\n-------------------------------\nСостояние погоды: <b>{weather_data["main"]} '
            f'({weather_data["description"]})</b>\n\n')
    if notes:
        for note in notes:
            text += f'-------------Заметка №{note[0]}-------------\n{note[1]}\n'
        send(chat_id, text, parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML', reply_markup=markup)


def show_weather(message):
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(button)

    user_city = city.get(message.chat.id)

    if user_city is None:
        city[message.chat.id] = 'zelenogradsk'
        user_city = 'zelenogradsk'

    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={user_city}&appid={API}&units=metric')
    data = json.loads(res.text)
    weather_data = data['weather'][0]

    send(message.chat.id, f'Погода в {user_city}:'
                          f'\n-------------------------------\nТемпература: <b>{data["main"]["temp"]}°</b>'
                          f'\n-------------------------------\nОщущается как: <b>{data["main"]["feels_like"]}°</b>'
                          f'\n-------------------------------\nСостояние погоды: <b>{weather_data["main"]} '
                          f'({weather_data["description"]})</b>\n\n', reply_markup=markup, parse_mode='HTML')


@bot.message_handler(commands=['createnote'])
def create_note(message):
    button = types.InlineKeyboardButton('Удалить сообщения', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    bot.delete_message(message.chat.id, message.message_id)
    send(message.chat.id, 'Заметка создана, напишите то, что должно находиться в заметке', reply_markup=markup)
    bot.register_next_step_handler(message, add_created_note)


def add_created_note(message):
    bot.delete_message(message.chat.id, message.message_id)
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    global notes
    count = 1
    for note in notes:
        if message.chat.id in note:
            count += 1
    notes.append([count, message.text, message.chat.id])
    send(message.chat.id, 'Запись сохранена!', reply_markup=markup)


@bot.message_handler(commands=['shownotes'])
def show_notes(message):
    bot.delete_message(message.chat.id, message.message_id)
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    text = ''
    if notes:
        for note in notes:
            if note[2] == message.chat.id:
                text += f'-------------Заметка №{note[0]}-------------\n{note[1]}\n'
    else:
        send(message.chat.id, 'У вас нет ни одной заметки', reply_markup=markup)
    if text != '':
        send(message.chat.id, text, reply_markup=markup)
    else:
        send(message.chat.id, 'У вас нет ни одной заметки', reply_markup=markup)


@bot.message_handler(commands=['deletenote'])
def delete_note(message):
    bot.delete_message(message.chat.id, message.message_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    button_cancel = types.InlineKeyboardButton('Отмена', callback_data='clear_weather')
    markup.add(button_cancel)
    for note in notes:
        if note[2] == message.chat.id:
            button = types.InlineKeyboardButton(
                text=f"{note[0]}", callback_data=f"delete_note_{note[0]}")
            markup.add(button)

    text = ''
    for note in notes:
        if note[2] == message.chat.id:
            text += f'-------------Заметка №{note[0]}-------------\n{note[1]}\n'
    send(message.chat.id, f'{text}\nВыберите заметку по номеру, которую надо удалить', reply_markup=markup)


@bot.message_handler(commands=['settime'])
def set_time_ask(message):
    bot.delete_message(message.chat.id, message.message_id)
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)

    send(message.chat.id, 'Укажите время, в которое бот должен вам написать.'
                          '\n-------------Правило правильного ввода-------------\nНапишите время таким образом "HH:MM"'
                          ' (ЧАС:МИНУТА).\nПримеры: <b>01:04</b> / <b>13:30</b> / <b>09:00</b>.',
         reply_markup=markup, parse_mode='HTML')
    bot.register_next_step_handler(message, set_time)


def clear_weather(message):
    bot.delete_message(message.chat.id, message.message_id)
    try:
        bot.delete_message(message.chat.id, message.message_id - 1)
    except Exception:
        pass


def set_time(message):
    bot.delete_message(message.chat.id, message.message_id)
    button = types.InlineKeyboardButton('Ок', callback_data='clear_weather')
    markup = types.InlineKeyboardMarkup()
    markup.add(button)
    hours = 0
    minutes = 0
    user_times[message.chat.id] = message.text
    try:
        hours, minutes = map(int, user_times.get(message.chat.id).split(':'))
    except ValueError:
        send(message.chat.id, 'Неправильный ввод времени! Пожалуйста, введите время в формате HH:MM',
             reply_markup=markup)
        return

    adjusted_hours = hours
    # если сервер находиться в другом часовом поясе (не в Калининградском),
    # то сюда стоит прибавить или отнять разницу, чтобы бот работал в правильном времени для жителей калининграда
    # (adjusted_hours = hours - 2)
    if adjusted_hours < 0:
        adjusted_hours += 24
    adjusted_time_str = f"{adjusted_hours:02d}:{minutes:02d}"
    send(message.chat.id, f'Время {hours}:{minutes} установлено', reply_markup=markup)
    try:
        schedule.every().day.at(adjusted_time_str).do(send_morning_message, chat_id=message.chat.id).tag(KGD_TIMEZONE)
    except Exception:
        send(message.chat.id, 'Постойте ка. Такого времени не существует!', reply_markup=markup)


threading.Thread(target=bot.polling, kwargs={"none_stop": True}).start()

while True:
    schedule.run_pending()
    time.sleep(1)
