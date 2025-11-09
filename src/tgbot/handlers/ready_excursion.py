from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode

from models.llm import LLM
from models.tts import TTS
from tgbot.states.ready_excursion_states import ReadyExcursionStartup as Startup
from tgbot.states.ready_excursion_states import ReadyExcursionExcursion as Excursion
from tgbot import keyboards
from tgbot.handlers.finish_handlers import finish_excursion
from tgbot.utils import exhibits


router = Router()
llm = LLM()
tts = TTS()

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
    audio = FSInputFile(await tts.generate_voice_message(description))
    format_id = await state.get_value('format_id')
    if format_id == 1:
        await bot.send_photo(q.from_user.id, exhibits[1])
    await bot.send_voice(q.from_user.id, audio)
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
    audio = FSInputFile(await tts.generate_voice_message(description))
    format_id = await state.get_value('format_id')
    await message.delete()
    if format_id == 1:
        await bot.send_photo(q.from_user.id, exhibits[exhibit_id])
    await bot.send_voice(q.from_user.id, audio)
    await bot.send_message(q.from_user.id, description, reply_markup=keyboards.next_exhibit)


@router.message(Excursion.exhibit)
async def exhibit(m: Message, state: FSMContext):
    await m.answer('Обрабатываю ответ на вопрос... Подождите немного!⏳')
    answer = await llm.generate_answer(m.text)
    await m.answer(answer, reply_markup=keyboards.next_exhibit)
