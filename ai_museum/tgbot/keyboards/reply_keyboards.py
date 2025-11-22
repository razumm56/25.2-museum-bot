from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

button_start_again = KeyboardButton(text='Начать заново')
button_finish_excursion = KeyboardButton(text="Завершить экскурсию")

keyboard_start = ReplyKeyboardMarkup(keyboard=[[button_start_again, button_finish_excursion]], resize_keyboard=True)

keyboard_start_after_finish_excursion = ReplyKeyboardMarkup(keyboard=[[button_start_again]], resize_keyboard=True)

main_keyboard = ReplyKeyboardMarkup(keyboard=[[
        KeyboardButton(text='Начать заново'),
        KeyboardButton(text='Завершить экскурсию')
    ]], resize_keyboard=True)

restart_keyboard = ReplyKeyboardMarkup(keyboard=[[
        KeyboardButton(text='Начать заново')
    ]], resize_keyboard=True)

