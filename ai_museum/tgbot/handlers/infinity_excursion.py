import os

from aiogram import Bot, F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from ai_museum.models.llm import LLM
from ai_museum.models.stt import STTManager
from ai_museum.models.tts import TTS
from ai_museum.tgbot import keyboards
from ai_museum.tgbot.states.infinity_excursion_states import (
    InfinityExcursion,
    InfinityExcursionStartup,
)
from ai_museum.tgbot.utils import exhibits

inf_router = Router()
llm = LLM()
tts = TTS()
stt = STTManager()


@inf_router.callback_query(F.data == 'endless_excursion')
async def start(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await q.message.delete()
    await state.set_state(InfinityExcursionStartup.format)
    await bot.send_message(q.from_user.id,
                           'Если любой момент захочешь выйти или начать заново — нажми кнопку внизу👇',
                           reply_markup=keyboards.main_keyboard)
    await bot.send_message(q.from_user.id, '*🎧 Экскурсия содержит аудио*\n\n'
                                           '*Вы готовы отправиться?*',
                           reply_markup=keyboards.user_ready, parse_mode=ParseMode.MARKDOWN)


@inf_router.callback_query(InfinityExcursionStartup.format, F.data == 'user ready')
async def set_route(q: CallbackQuery, state: FSMContext, bot: Bot):
    await q.answer()
    await q.message.delete()
    await state.set_state(InfinityExcursion.exhibit)
    message = await bot.send_message(q.from_user.id, 'Обрабатываю описание экспоната... Подождите немного!⏳')
    description = await llm.generate_description(exhibit_id=1)
    await state.update_data(history=[{"from": "assistant", "text": description}])
    await message.delete()
    await bot.send_message(q.from_user.id, description)


@inf_router.message(InfinityExcursion.exhibit, F.voice)
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


@inf_router.message(InfinityExcursion.exhibit)
async def exhibit_infinity(m: Message, state: FSMContext):
    history = await state.get_value('history')
    history.append({"from": "user", "text": m.text})
    await m.answer('Обрабатываю ответ на вопрос... Подождите немного!⏳')
    answer = await llm.generate_answer(m.text)
    history.append({"from": "assistant", "text": answer})
    await state.update_data(history=history)
    await m.answer(answer)
