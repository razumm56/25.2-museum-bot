from __future__ import annotations

import os

from aiogram import Bot, F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
    Voice,
)
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import Command, RunnableConfig
from loguru import logger

from ai_museum.agents.infinity_excursion_agent.expert import InitExpertState
from ai_museum.agents.infinity_excursion_agent.guide import InitGuideState
from ai_museum.agents.infinity_excursion_agent import compiled_graphs
from ai_museum.db.functions import (
    create_expert_session,
    create_guide_session,
    get_user_chat_history,
    get_user_exhibit_chat_history,
    search_similar_exhibits,
)
from ai_museum.db.models import Exhibit
from ai_museum.models.stt import STTManager
from ai_museum.models.tts import TTS
from ai_museum.tgbot import keyboards
from ai_museum.tgbot.states.infinity_excursion_states import InfinityExcursion
from ai_museum.utils import require_var_type


def get_exhibits_keyboard(exhibits: list[Exhibit]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=exhibit.name,
                    callback_data=f"choose_exhibit:{exhibit.id}",
                )
            ]
            for exhibit in exhibits
        ]
    )


async def guide_init(user_id: int) -> str:
    guide_obj = await create_guide_session(user_id)
    guide_id = str(guide_obj.id)

    config: RunnableConfig = {"configurable": {"thread_id": guide_id}}
    if isinstance(compiled_graphs.guide_app.checkpointer, BaseCheckpointSaver):
        _ = await compiled_graphs.guide_app.checkpointer.adelete_thread(guide_id)

    init_state = InitGuideState()
    _ = await compiled_graphs.guide_app.ainvoke(init_state, config=config)

    return guide_id


async def guide_invoke(guide_id: str, model_prompt: str):
    config: RunnableConfig = {"configurable": {"thread_id": guide_id}}

    response = await compiled_graphs.guide_app.ainvoke(
        Command(resume=model_prompt), config=config
    )
    last_ai_message: str = response["messages"][-1].content

    return "Ответ путеводителя:\n" + last_ai_message


async def guide_reply(bot: Bot, user_id: int, guide_id: str, prompt: str):
    response_wait_message = await bot.send_message(
        user_id, "Обрабатываю ваш ответ... Подождите немного!⏳"
    )
    ai_response = await guide_invoke(guide_id, prompt)
    _ = await response_wait_message.delete()

    _ = await bot.send_message(
        user_id, text=ai_response, reply_markup=keyboards.guide_keyboard
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
        _ = q.message.delete()

    _ = await bot.send_message(
        q.from_user.id,
        "Добро пожаловать в режим бесконечной экскурсии! Если любой момент захочешь выйти или начать заново — нажми кнопку внизу👇",
        reply_markup=keyboards.main_keyboard,
    )

    conversation_history = await get_user_chat_history(user_id)

    await state.set_state(InfinityExcursion.guide_wait_user_reply)
    if len(conversation_history) > 0:
        _ = await bot.send_message(
            user_id,
            "Обнаружены прошлые чаты, хотите продолжить последний?",
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
            prompt="я вернулся, кратко напомни что было",
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
            prompt="Поздаровайся, этот пользователь уже посещал музей",
        )
        _ = await state.update_data(guide_id=guide_id)
        await state.set_state(InfinityExcursion.guide_chat)

    elif q.data == "guide_proceed_start":
        guide_id = await guide_init(user_id)

        await guide_reply(
            bot=bot,
            user_id=user_id,
            guide_id=guide_id,
            prompt="Поздаровайся",
        )
        _ = await state.update_data(guide_id=guide_id)
        await state.set_state(InfinityExcursion.guide_chat)

    elif q.data.startswith("choose_exhibit:"):
        if isinstance(q.message, Message):
            _ = await q.message.delete()

        guide_id = require_var_type(await state.get_value("guide_id"), str)

        _ = await q.answer()

        exhibit_id = int(q.data.split(":")[1])
        await state.set_state(InfinityExcursion.expert_chat)

        expert_chat_history = await get_user_exhibit_chat_history(guide_id, exhibit_id)

        if expert_chat_history:
            expert_id = str(expert_chat_history[-1].id)
            _ = await state.update_data(expert_id=expert_id)
            expert_prompt = "я вернулся, кратко напомни о чем ты мне рассказывала"
        else:
            expert_id = await expert_init(guide_id, exhibit_id)
        expert_prompt = "поздаровайся епта"

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

    exhibits = await search_similar_exhibits(text[:500], k=5)

    _ = await state.update_data(
        guide_id=guide_id,
        suggested_exhibit_ids=[ex.id for ex in exhibits],
    )

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


async def expert_init(guide_id: str, exhibit_id: int) -> str:
    expert_obj = await create_expert_session(guide_id, exhibit_id)
    expert_id = str(expert_obj.id)

    config: RunnableConfig = {"configurable": {"thread_id": expert_id}}
    # удаляем thread_id если есть коллизия
    if isinstance(compiled_graphs.expert_app.checkpointer, BaseCheckpointSaver):
        _ = await compiled_graphs.expert_app.checkpointer.adelete_thread(expert_id)

    init_state = InitExpertState({"exp_id": exhibit_id})
    _ = await compiled_graphs.expert_app.ainvoke(init_state, config=config)

    return expert_id


async def expert_invoke(expert_thread_id: str, prompt: str):
    config: RunnableConfig = {"configurable": {"thread_id": expert_thread_id}}

    response = await compiled_graphs.expert_app.ainvoke(
        Command(resume=prompt), config=config
    )
    last_ai_message: str = response["messages"][-1].content

    return "Ответ эксперта:\n" + last_ai_message


async def expert_reply(bot: Bot, user_id: int, expert_id: str, prompt: str):
    wait_message = await bot.send_message(
        user_id, "Обрабатываю ваш ответ... Подождите немного!⏳"
    )
    ai_response = await expert_invoke(expert_id, prompt)
    _ = await wait_message.delete()

    _ = await bot.send_message(
        user_id, text=ai_response, reply_markup=keyboards.expert_keyboard
    )


@inf_router.message(InfinityExcursion.expert_chat, F.text == "Выход")
async def back_to_guide(m: Message, state: FSMContext, bot: Bot):
    user_id = require_var_type(m.from_user, User).id
    logger.info(f"{user_id} back to guide")

    await state.set_state(InfinityExcursion.guide_chat)

    text = "Пользователь вернулся с экспоната, по хорошему у тебя будет контекст, а пока жалуйся"
    guide_id = require_var_type(await state.get_value("guide_id"), str)
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
