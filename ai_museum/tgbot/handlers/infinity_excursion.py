from __future__ import annotations

import os

from aiogram import Bot, F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    User,
    Voice,
)
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph.state import RunnableConfig
from loguru import logger

from ai_museum.agents.infinity_excursion_agent import compiled_graphs
from ai_museum.agents.infinity_excursion_agent.expert import (
    expert_init,
    expert_invoke,
)
from ai_museum.agents.infinity_excursion_agent.guide import guide_init, guide_invoke
from ai_museum.db.functions import (
    get_user_chat_history,
    get_user_exhibit_chat_history,
    asearch_similar_exhibits,
)
from ai_museum.models.llm import LLMFactory
from ai_museum.models.stt import STTManager
from ai_museum.models.tts import TTS
from ai_museum.tgbot import keyboards
from ai_museum.tgbot.keyboards.inline_keyboards import get_exhibits_keyboard
from ai_museum.tgbot.states.infinity_excursion_states import InfinityExcursion
from ai_museum.utils import require_var_type


async def summarize_expert_session(messages: list[AnyMessage]) -> str:
    """Обобщает беседу с экспертом в краткий результат"""
    llm = LLMFactory.get_llm("gigachat")

    # Форматируем сообщения для суммаризации
    conversation_text = "\n".join(
        [
            f"{'Пользователь' if msg.type == 'human' else 'Эксперт'}: {msg.content}"
            for msg in messages
        ]
    )

    summary_prompt = f"""Напиши краткое резюме (2-3 предложения) того, что рассказал эксперт о экспонате. 
Фокусируйся на самых интересных фактах и ключевой информации.

Беседа:
{conversation_text}"""

    response = await llm.ainvoke(summary_prompt)
    if isinstance(response.content, list):
        return "\n".join(str(response))
    return response.content


async def guide_reply(bot: Bot, user_id: int, guide_id: str, prompt: str):
    logger.debug(f"{user_id} at guide_reply")
    wait_message = await bot.send_message(
        user_id, "Обрабатываю ваш ответ... Подождите немного!⏳"
    )
    ai_response = await guide_invoke(guide_id, prompt)
    _ = await wait_message.delete()

    _ = await bot.send_message(
        user_id,
        text=ai_response,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboards.guide_keyboard,
    )


async def expert_reply(bot: Bot, user_id: int, expert_id: str, prompt: str):
    logger.debug(f"{user_id} at expert_reply")
    wait_message = await bot.send_message(
        user_id, "Обрабатываю ваш ответ... Подождите немного!⏳"
    )
    ai_response = await expert_invoke(expert_id, prompt)
    _ = await wait_message.delete()

    _ = await bot.send_message(
        user_id, text=ai_response, reply_markup=keyboards.expert_keyboard
    )


inf_router = Router()
tts = TTS()
stt = STTManager()


@inf_router.callback_query(F.data == "endless_excursion")
async def start(q: CallbackQuery, state: FSMContext, bot: Bot):
    logger.debug(f"{q.from_user.id} chose endless_excursion")
    user_id = q.from_user.id

    _ = await q.answer()
    if isinstance(q.message, Message):
        _ = await q.message.delete()

    _ = await bot.send_message(
        q.from_user.id,
        "♾️ Добро пожаловать в режим бесконечной экскурсии! Если в любой момент захочешь выйти или начать заново — нажми кнопку внизу👇",
        reply_markup=keyboards.main_keyboard,
    )

    conversation_history = await get_user_chat_history(user_id)

    await state.set_state(InfinityExcursion.guide_wait_user_reply)
    if len(conversation_history) > 0:
        _ = await bot.send_message(
            user_id,
            "Похоже вы уже посещали наш музей, хотите продолжить прошлую экскурсию?",
            reply_markup=keyboards.guide_continue_prompt,
        )
    else:
        _ = await bot.send_message(
            q.from_user.id,
            "*🎧 Экскурсия содержит аудио*\n\n*Вы готовы отправиться?*",
            reply_markup=keyboards.guide_start_ready,
            parse_mode=ParseMode.MARKDOWN,
        )


@inf_router.callback_query(InfinityExcursion.guide_wait_user_reply)
async def guide_process_inline_markup_reply(
    q: CallbackQuery, state: FSMContext, bot: Bot
):
    """Функция которая обрабатывает все нажатия юзера на кнопки"""
    user_id = q.from_user.id
    logger.info(f"{user_id} at guide waiting state")

    if not q.data:
        return

    if q.data == "guide_continue_chat":
        if isinstance(q.message, Message):
            _ = await q.message.delete()
        _ = await bot.send_message(
            q.from_user.id, text="Возобновляем ваш прошлый сеанс..."
        )

        chat_history = await get_user_chat_history(user_id)
        guide_id = str(chat_history[-1].id)

        await guide_reply(
            bot=bot,
            user_id=user_id,
            guide_id=guide_id,
            prompt="Пользователь вернулся в музей и решил продолжить экскурсию, напомни ему о том что он делал во время последней экскурсии",
        )
        _ = await state.update_data(guide_id=guide_id)
        await state.set_state(InfinityExcursion.guide_chat)

    elif q.data == "guide_new_chat":
        if isinstance(q.message, Message):
            _ = await q.message.delete()

        guide_id = await guide_init(user_id)

        await guide_reply(
            bot=bot,
            user_id=user_id,
            guide_id=guide_id,
            prompt="Поприветствуй пользователя, он уже посещал текущий музей",
        )
        _ = await state.update_data(guide_id=guide_id)
        await state.set_state(InfinityExcursion.guide_chat)

    elif q.data == "guide_proceed_start":
        guide_id = await guide_init(user_id)

        await guide_reply(
            bot=bot,
            user_id=user_id,
            guide_id=guide_id,
            prompt="Поприветствуй пользователя",
        )
        _ = await state.update_data(guide_id=guide_id)
        await state.set_state(InfinityExcursion.guide_chat)

    elif q.data.startswith("choose_exhibit:"):
        _ = await q.answer()
        if isinstance(q.message, Message):
            _ = await q.message.delete()

        guide_id = require_var_type(await state.get_value("guide_id"), str)

        exhibit_id = int(q.data.split(":")[1])
        await state.set_state(InfinityExcursion.expert_chat)

        expert_chat_history = await get_user_exhibit_chat_history(guide_id, exhibit_id)

        if expert_chat_history:
            expert_id = str(expert_chat_history[-1].id)
            expert_prompt = "Пользователь вернулся к этому экспонату, кратко напомни что ты рассказывала"
        else:
            expert_id = await expert_init(guide_id, exhibit_id)
            expert_prompt = "Пользователь впервые у данного экспоната, сделай очень краткое вступление"

        _ = await state.update_data(expert_id=expert_id)

        await expert_reply(
            bot=bot,
            user_id=user_id,
            expert_id=expert_id,
            prompt=expert_prompt,
        )


@inf_router.message(InfinityExcursion.guide_chat, F.text == "Предложи экспонаты")
async def guide_lead(m: Message, state: FSMContext):
    user_id = require_var_type(m.from_user, User).id
    logger.debug(f"{user_id} at guide_lead")

    guide_id = require_var_type(await state.get_value("guide_id"), str)

    config: RunnableConfig = {"configurable": {"thread_id": guide_id}}
    snapshot = await compiled_graphs.guide_app.aget_state(config)

    text = ""
    for message in snapshot.values["messages"]:
        if isinstance(message, HumanMessage):
            text += f"User: {message.content};"
        elif isinstance(message, AIMessage):
            text += f"AI: {message.content};"

    exhibits = await asearch_similar_exhibits(text[:500], k=5)

    _ = await m.answer(
        "Я подобрал несколько экспонатов, выбери один 👇",
        reply_markup=get_exhibits_keyboard(exhibits),
    )
    await state.set_state(InfinityExcursion.guide_wait_user_reply)


@inf_router.message(InfinityExcursion.guide_chat, F.voice)
async def guide_reply_to_voice(m: Message, state: FSMContext, bot: Bot):
    user_id = require_var_type(m.from_user, User).id
    logger.debug(f"{user_id} at voice_question")

    # расшифровка голоса
    voice = require_var_type(m.voice, Voice)
    voice_wait_message = await bot.send_message(user_id, "Распознаю ваш голос...")
    file = await bot.get_file(voice.file_id)
    _ = await bot.download_file(file.file_path, f"{voice.file_id}.ogg")  # pyright: ignore[reportArgumentType]
    text = await stt.transcribe_audio(f"{voice.file_id}.ogg")
    os.remove(f"{voice.file_id}.ogg")
    _ = await voice_wait_message.delete()

    # генерация ответа
    guide_id = require_var_type(await state.get_value("guide_id"), str)
    await guide_reply(bot=bot, user_id=user_id, guide_id=guide_id, prompt=text)


@inf_router.message(InfinityExcursion.guide_chat)
async def guide_reply_to_text(m: Message, state: FSMContext, bot: Bot):
    user_id = require_var_type(m.from_user, User).id
    logger.debug(f"{user_id} at guide_chat")

    text = require_var_type(m.text, str)
    guide_id = require_var_type(await state.get_value("guide_id"), str)
    await guide_reply(bot=bot, user_id=user_id, guide_id=guide_id, prompt=text)


@inf_router.message(InfinityExcursion.expert_chat, F.text == "Вернуться к путеводителю")
async def back_to_guide(m: Message, state: FSMContext, bot: Bot):
    user_id = require_var_type(m.from_user, User).id
    logger.info(f"{user_id} back to guide")

    await state.set_state(InfinityExcursion.guide_chat)

    # получаем резюме беседы с экспертом
    expert_id = require_var_type(await state.get_value("expert_id"), str)
    config: RunnableConfig = {"configurable": {"thread_id": expert_id}}
    snapshot = await compiled_graphs.expert_app.aget_state(config)

    expert_messages: list[AnyMessage] = snapshot.values.get("messages", [])
    summary = ""
    if expert_messages:
        summary = await summarize_expert_session(expert_messages)
        summary = f"\n\n📝 Краткое резюме беседы с экспертом:\n{summary}"

    guide_id = require_var_type(await state.get_value("guide_id"), str)
    text = f"Пользователь вернулся с экспоната. {summary}"
    await guide_reply(bot=bot, user_id=user_id, guide_id=guide_id, prompt=text)


@inf_router.message(InfinityExcursion.expert_chat, F.voice)
async def expert_reply_to_voice(m: Message, state: FSMContext, bot: Bot):
    user_id = require_var_type(m.from_user, User).id
    logger.debug(f"{user_id} at voice_question")

    # расшифровка голоса
    voice = require_var_type(m.voice, Voice)
    voice_wait_message = await bot.send_message(user_id, "Распознаю ваш голос...")
    file = await bot.get_file(voice.file_id)
    _ = await bot.download_file(file.file_path, f"{voice.file_id}.ogg")  # pyright: ignore[reportArgumentType]
    text = await stt.transcribe_audio(f"{voice.file_id}.ogg")
    os.remove(f"{voice.file_id}.ogg")
    _ = await voice_wait_message.delete()

    # генерация ответа
    expert_id = require_var_type(await state.get_value("expert_id"), str)
    await expert_reply(bot=bot, user_id=user_id, expert_id=expert_id, prompt=text)


@inf_router.message(InfinityExcursion.expert_chat)
async def expert_reply_to_text(m: Message, state: FSMContext, bot: Bot):
    user_id = require_var_type(m.from_user, User).id
    logger.debug(f"{user_id} at expert_chat")

    text = require_var_type(m.text, str)
    expert_id = require_var_type(await state.get_value("expert_id"), str)
    await expert_reply(bot=bot, user_id=user_id, expert_id=expert_id, prompt=text)
