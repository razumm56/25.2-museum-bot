import os

from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from models.llm import LLM
from models.tts import TTS
from models.stt import STTManager
from tgbot.states.personal_excursion_states import PersonalExcursionStartup as Startup
from tgbot.states.personal_excursion_states import PersonalExcursionExcursion as Excursion
from tgbot.utils import generate_map
from tgbot import keyboards
from tgbot.handlers.finish_handlers import finish_excursion
from db.create_tabels import get_image_url


pers_route = Router()
llm = LLM()
tts = TTS()
stt = STTManager()


@pers_route.callback_query(F.data == 'personal_excursion')
async def start(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await q.message.delete()
    await bot.send_message(q.from_user.id,
                           'Перед началом экскурсии, выбери в каком стиле ты хочешь её пройти — или в какой манере я буду рассказывать:\n'
                           'Например:\n\n'
                           '🪆 В стиле русской сказки\n'
                           '🧠 Научно популярное путешествие\n'
                           '🌟 Рассказ Снегурочки, другого любимого персонажа или даже известной личности\n'
                           '🎄 Историю Сибири с тайнами и легендами\n\n'
                           '💬 Просто напиши стиль или персонажа, а я адаптирую экскурсию под твои желания!'
                           )
    await state.set_state(Startup.style)
    await bot.send_message(q.from_user.id,
                           'Если любой момент захочешь выйти или начать заново — нажми кнопку внизу👇',
                            reply_markup=keyboards.main_keyboard
    )


@pers_route.message(Startup.style, F.voice)
async def set_style_voice(m: Message, state: FSMContext, bot: Bot):
    file = await bot.get_file(m.voice.file_id)
    await bot.download_file(file.file_path, f"{m.voice.file_id}.ogg")
    text = await stt.transcribe_audio(f"{m.voice.file_id}.ogg")
    if not text:
        await m.answer('Сообщение не распознано')
        return
    await state.update_data(style=text)
    await state.set_state(Startup.format)
    await m.answer('*Выбери удобный для себя формат экскурсии*\n\n'
                   '📸 С изображениями экспонатов — увидишь фото каждого объекта\n'
                   '📝 Без изображений — описание в виде текста и аудио',
                   parse_mode=ParseMode.MARKDOWN,
                   reply_markup=keyboards.formats_keyboard)


@pers_route.message(Startup.style)
async def set_style(m: Message, state: FSMContext):
    await state.update_data(style=m.text)
    await state.set_state(Startup.format)
    await m.answer('*Выбери удобный для себя формат экскурсии*\n\n'
                   '📸 С изображениями экспонатов — увидишь фото каждого объекта\n'
                   '📝 Без изображений — описание в виде текста и аудио',
                   parse_mode=ParseMode.MARKDOWN,
                   reply_markup=keyboards.formats_keyboard)


@pers_route.callback_query(Startup.format, F.data.regexp(r'^format \d$'))
async def set_format(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await q.message.delete()
    format_id = int(q.data.split()[-1])
    await state.update_data(format_id=format_id)
    await bot.send_message(q.from_user.id, '*Карта вашего маршрута*\n\n'
                                           '➡️ Следуйте по порядку номеров экспонатов.\n'
                                           '📍 На карте они отмечены точками, а на полу — наклейками с такими же индексами,'
                                           'чтобы вы легко ориентировались в пространстве выставки',
                           parse_mode=ParseMode.MARKDOWN)
    await bot.send_photo(q.from_user.id, 'https://fotohosting.pro/i/route-map.hpUXN')
    await state.update_data(route='personal', exhibit_id=1)
    await bot.send_message(q.from_user.id, '*🎧 Экскурсия содержит аудио*\n\n'
                                           '*Вы готовы отправиться?*',
                           reply_markup=keyboards.user_ready, parse_mode=ParseMode.MARKDOWN)

@pers_route.callback_query(Startup.format, F.data == 'user ready')
async def set_route(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await q.message.delete()
    await state.set_state(Excursion.exhibit)
    message = await bot.send_message(q.from_user.id, 'Обрабатываю описание экспоната... Подождите немного!⏳')
    description = await llm.generate_description(exhibit_id=1)
    format_id = await state.get_value('format_id')
    await message.delete()
    if format_id == 1:
        await bot.send_photo(q.from_user.id, get_image_url(1), caption=description[:1024], reply_markup=keyboards.next_exhibit)
    else:
        await bot.send_message(q.from_user.id, description, reply_markup=keyboards.next_exhibit)


@pers_route.callback_query(Excursion.exhibit, F.data == 'next exhibit')
async def send_next_exhibit(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await q.message.delete()
    exhibit_id = await state.get_value('exhibit_id')
    if exhibit_id == 5:
        await finish_excursion(q, bot)
        return
    exhibit_id += 1
    await state.update_data(exhibit_id=exhibit_id)
    message = await bot.send_message(q.from_user.id, 'Обрабатываю описание экспоната... Подождите немного!⏳')
    description = await llm.generate_description(exhibit_id=exhibit_id)
    format_id = await state.get_value('format_id')
    await message.delete()
    if format_id == 1:
        await bot.send_photo(q.from_user.id, get_image_url(exhibit_id), caption=description[:1024], reply_markup=keyboards.next_exhibit)
    else:
        await bot.send_message(q.from_user.id, description, reply_markup=keyboards.next_exhibit)


@pers_route.message(Excursion.exhibit, F.voice)
async def voice_question(m: Message, state: FSMContext, bot: Bot):
    file = await bot.get_file(m.voice.file_id)
    await bot.download_file(file.file_path, f"{m.voice.file_id}.ogg")
    text = await stt.transcribe_audio(f"{m.voice.file_id}.ogg")
    if not text:
        await m.answer('Сообщение не распознано')
        return
    answer = await llm.generate_answer(text)
    await m.answer(answer)
    if os.path.exists(f"{m.voice.file_id}.ogg"):
        os.remove(f"{m.voice.file_id}.ogg")



@pers_route.message(Excursion.exhibit)
async def exhibit(m: Message, state: FSMContext):
    await m.answer('Обрабатываю ответ на вопрос... Подождите немного!⏳')
    answer = await llm.generate_answer(m.text)
    await m.answer(answer, reply_markup=keyboards.next_exhibit)

