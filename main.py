import random
import telebot
import os
from telebot import types
from telebot.handler_backends import State, StatesGroup

from data_base_models import (
    new_user_for_db,
    words,
    update_step_user_db,
    select_step_user_db,
    add_word_user,
    delete_word_user,
)

os.environ["token"] = input("Токен бота пжжл")
bot = telebot.TeleBot(os.environ["token"])


class Command:
    # Создание класса для кнопок.
    ADD_WORD = "Добавить слово ➕"
    DELETE_WORD = "Удалить слово🔙"
    NEXT = "Дальше ⏭"


class MyStates(StatesGroup):
    # Создание класса для стейтов.
    translate_word = State()
    next_word = State()
    add_word = State()
    new_word = State()
    delete_word = State()


def check_user_step(chat_id: int):
    # Проверка текущего шага у пользователя, при отсутсвии шага возвращает 1 и добавляет в БД.
    step = select_step_user_db(chat_id)
    if step is not None:
        return step
    elif step is None:
        new_user_for_db(chat_id)
        return 1


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(
        message,
        """Привет 👋 Давай попрактикуемся в английском языке. Тренировки можешь проходить в удобном для себя темпе.
        У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения.
        Для этого воспрользуйся инструментами:
        - добавить слово ➕,
        - удалить слово 🔙.
        Ну что, начнём ⬇️
        Введи команду /Go для начала
    """,
    )


@bot.message_handler(commands=["Go", "go"])
def english_traning(message):
    """
    По вводу команды /Go или /go:
        1. Получает шаг пользователя из БД
        2. Получает все слова пользователя (добавленные, удаленные, дефолтные)
            При вовзрата None обнуляет шаг пользователя до 1
        3. Добавляет кнопки
        4. Фиксирует стейт
        5. Записывает проверочное слово
    """

    step = check_user_step(message.chat.id)
    game_words = words(message.chat.id, step)
    if game_words is None:
        update_step_user_db(message.chat.id, 1)
        step = check_user_step(message.chat.id)
        game_words = words(message.chat.id, step)
    markup = types.ReplyKeyboardMarkup(row_width=2)
    translate_words_btn = types.KeyboardButton(game_words[2])
    option_words_btn = [types.KeyboardButton(word) for word in game_words[3:]]
    buttons = [translate_words_btn] + option_words_btn
    random.shuffle(buttons)
    nxt_btn = types.KeyboardButton(Command.NEXT)
    add_bt = types.KeyboardButton(Command.ADD_WORD)
    delete_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([nxt_btn, add_bt, delete_btn])
    markup.add(*buttons)
    bot.send_message(
        message.chat.id,
        f"Назови правильный перевод слова: {game_words[1]}",
        reply_markup=markup,
    )
    bot.set_state(message.from_user.id, MyStates.translate_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["translate_word"] = game_words[2]


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_word(message):
    step = check_user_step(message.chat.id)
    try:  # Для обработки шага нового пользователя.
        step = step[0] + 1
    except TypeError:
        pass
    update_step_user_db(message.chat.id, step)
    english_traning(message)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def set_state_add_word(message):
    bot.send_message(
        message.chat.id,
        "Введите русское слово, его перевод и 3 варианта, через запятую",
    )
    bot.set_state(message.from_user.id, MyStates.new_word, message.chat.id)


@bot.message_handler(
    func=lambda message: bot.get_state(message.chat.id) == MyStates.new_word.name
)
def add_word(message):
    result = add_word_user((message.text).split(","), message.chat.id)
    if type(result) == tuple:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        nxt_btn = types.KeyboardButton(Command.NEXT)
        markup.add(nxt_btn)
        bot.send_message(
            message.chat.id,
            f"Слово добавлено, сейчас вы изучаете {result[0]} слова(ов)",
            reply_markup=markup,
        )
    elif result == "Данное слово уже было добавлено":
        bot.send_message(message.chat.id, "Данное слово уже было добавлено")
    else:
        bot.send_message(message.chat.id, "Что-то пошло не так, попробуй по инструкции")


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def set_state_delete_word(message):
    bot.send_message(message.chat.id, "Введите слово, которое хотите удалить")
    bot.set_state(message.from_user.id, MyStates.delete_word, message.chat.id)


@bot.message_handler(
    func=lambda message: bot.get_state(message.chat.id) == MyStates.delete_word.name
)
def delete_word(message):
    result = delete_word_user(message.text, message.chat.id)
    if type(result) == tuple:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        nxt_btn = types.KeyboardButton(Command.NEXT)
        markup.add(nxt_btn)
        bot.send_message(message.chat.id, "Слово удалено", reply_markup=markup)
    elif result == "Данное слово уже было удалено":
        bot.send_message(message.chat.id, "Данное слово уже было удалено")
    elif result == "Данного слова нет в изучаемых вами слов":
        bot.send_message(message.chat.id, "Данного слова нет в изучаемых вами слов")
    else:
        bot.send_message(message.chat.id, "Что-то пошло не так")


@bot.message_handler(func=lambda message: True, content_types=["text"])
def message_reply(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        translate_word = data.get("translate_word")
        if translate_word is None:
            bot.send_message(message.chat.id, "Для продолжения игры нажмите /Go")
            return
        if message.text == translate_word:
            markup = types.ReplyKeyboardMarkup(row_width=2)
            nxt_btn = types.KeyboardButton(Command.NEXT)
            add_bt = types.KeyboardButton(Command.ADD_WORD)
            delete_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons = [nxt_btn, add_bt, delete_btn]
            markup.add(*buttons)
            bot.send_message(message.chat.id, "Правильный ответ", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Не правильный ответ")


if __name__ == "__main__":
    print("работает")
    bot.polling()
