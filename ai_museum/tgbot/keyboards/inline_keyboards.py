from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Инлайн-кнопка для редактирования профиля
button_excursion_with_photo = InlineKeyboardButton(
    text='C изображениями',
    callback_data='excursion_with_photo_pressed'
)

button_excursion_without_photo = InlineKeyboardButton(
    text='Без изображений',
    callback_data='excursion_without_photo_pressed'
)

button_personal_excursion_type = InlineKeyboardButton(
    text='✨ Персональная',
    callback_data='personal_excursion'
)

button_endless_excursion_type  = InlineKeyboardButton(
    text='🔄 Бесконечная', 
    callback_data='endless_excursion'
)

button_ready_excursion_type  = InlineKeyboardButton(
    text='📋 Готовая',
    callback_data='ready_excursion'
)

button_back_excursion_types = InlineKeyboardButton(
    text='⬅️ Назад',
    callback_data='back_choose_excursion_types'
)

button_back_personal_excursion_type = InlineKeyboardButton(
    text='⬅️ Назад',
    callback_data='back_personal_excursion_type'
)

button_choose_test_museum = InlineKeyboardButton(text="Тюменский музей", callback_data='choosed_museum_test')

choose_excursion_settings = InlineKeyboardMarkup(inline_keyboard=[[button_excursion_with_photo, button_excursion_without_photo]])


keyboard_excursion_types = InlineKeyboardMarkup(
    inline_keyboard=[
        [button_personal_excursion_type],
        [button_endless_excursion_type], 
        [button_ready_excursion_type],
        [button_back_excursion_types]
    ]
)

keyboard_choose_museums = InlineKeyboardMarkup(inline_keyboard=[[button_choose_test_museum]])

keyboard_after_choose_personal_excursion_type = InlineKeyboardMarkup(inline_keyboard=[[button_back_personal_excursion_type]])


formats_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='С изображением', callback_data='format 1'),
        InlineKeyboardButton(text='Без изображения', callback_data='format 2'),
    ]])

user_ready = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='Да, я готов(а)', callback_data='user ready')
    ]])

guide_continue_prompt = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="Да, конечно", callback_data="guide_continue_chat"),
    InlineKeyboardButton(text="Нет, хочу начать новый", callback_data="guide_new_chat")
]])
guide_start_ready = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="Да, я готов(а)", callback_data="guide_proceed_start")
]])

routes_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='Заготовленный', callback_data='route prepared'),
    ], [
        InlineKeyboardButton(text='Экспресс', callback_data='route express'),
    ], [
    InlineKeyboardButton(text='Индивидуальная', callback_data='route individual')
]])

next_exhibit = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text='Следующий экспонат', callback_data='next exhibit')
]])
