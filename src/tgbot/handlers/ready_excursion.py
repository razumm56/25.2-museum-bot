import os

from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from models.llm import LLM
from models.tts import TTS
from models.stt import STTManager
from tgbot.states.ready_excursion_states import ReadyExcursionStartup as Startup
from tgbot.states.ready_excursion_states import ReadyExcursionExcursion as Excursion
from tgbot import keyboards
from tgbot.handlers.finish_handlers import finish_excursion
from tgbot.utils import exhibits
from db.create_tabels import get_image_url


router = Router()
llm = LLM()
tts = TTS()
stt = STTManager()

@router.callback_query(F.data == 'ready_excursion')
async def start(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await q.message.delete()
    await state.set_state(Startup.format)
    await bot.send_message(q.from_user.id,
                           'Если любой момент захочешь выйти или начать заново — нажми кнопку внизу👇',
                           reply_markup=keyboards.main_keyboard)
    await bot.send_message(q.from_user.id,
                           '*Выбери удобный для себя формат экскурсии*\n\n'
                   '📸 С изображениями экспонатов — увидишь фото каждого объекта\n'
                   '📝 Без изображений — описание в виде текста и аудио',
                   parse_mode=ParseMode.MARKDOWN,
                   reply_markup=keyboards.formats_keyboard)


@router.callback_query(Startup.format, F.data.regexp(r'^format \d$'))
async def set_format(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await q.message.delete()
    format_id = int(q.data.split()[-1])
    await state.update_data(format_id=format_id)
    await state.update_data(route='personal', exhibit_id=1)
    await bot.send_message(q.from_user.id, '*🎧 Экскурсия содержит аудио*\n\n'
                                           '*Вы готовы отправиться?*',
                           reply_markup=keyboards.user_ready, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(Startup.format, F.data == 'user ready')
async def set_route(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await state.set_state(Excursion.exhibit)
    await bot.send_message(q.from_user.id, 'Обрабатываю описание экспоната... Подождите немного!⏳')
    description = await llm.generate_description(exhibit_id=1)
    format_id = await state.get_value('format_id')
    if format_id == 1:
        await bot.send_photo(q.from_user.id, get_image_url(1), caption=description[:1024], reply_markup=keyboards.next_exhibit)
    else:
        await bot.send_message(q.from_user.id, description, reply_markup=keyboards.next_exhibit)


@router.callback_query(Excursion.exhibit, F.data == 'next exhibit')
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


@router.message(Excursion.exhibit, F.voice)
async def voice_question(m: Message, state: FSMContext, bot: Bot):
    file = await bot.get_file(m.voice.file_id)
    await bot.download_file(file.file_path, f"{m.voice.file_id}.ogg")
    text = await stt.transcribe_audio(f"{m.voice.file_id}.ogg")
    if not text:
        await m.answer('Сообщение не распознано')
        return
    os.remove(f"{m.voice.file_id}.ogg")
    answer = await llm.generate_answer(text)
    await m.answer(answer)


@router.message(Excursion.exhibit)
async def exhibit(m: Message, state: FSMContext):
    await m.answer('Обрабатываю ответ на вопрос... Подождите немного!⏳')
    answer = await llm.generate_answer(m.text)
    await m.answer(answer, reply_markup=keyboards.next_exhibit)
