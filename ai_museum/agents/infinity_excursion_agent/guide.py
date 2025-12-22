import asyncio
from typing import NotRequired, TypedDict

from langchain.agents import AgentState, create_agent
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
)
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.state import Command, RunnableConfig
from langgraph.types import interrupt
from loguru import logger

from ai_museum.agents.infinity_excursion_agent import compiled_graphs
from ai_museum.db.functions import create_guide_session
from ai_museum.models.llm import LLMFactory
from .tools import web_search

llm = LLMFactory.get_llm("gigachat")

# агент

# #  инструменты для управления пайплайном
# @tool
# def finish_graph():
#     """Завершает работу графа"""
#     return Command(goto=END)
#
#
# @tool
# def lead_to_exhibit(exp_id: str):
#     """Функция ведет пользователя к экспонату с указанным идентификатором"""
#
#     return Command(goto="lead_to_exp", update={"exp_id": exp_id})


class EmptyContext(TypedDict):
    pass


SYSTEM_PROMPT = """
Ты виртуальный экскурсовод в музее Словцова. Ты выступаешь в роли проводника к экспонатам.
"""
guide_agent = create_agent(
    llm,
    tools=[web_search],
    system_prompt=SYSTEM_PROMPT,
    state_schema=AgentState,
    context_schema=EmptyContext,
)


# граф
class GuideState(TypedDict):
    user_id: str
    user_input: str
    exp_id: str | None
    messages: list[AnyMessage]


class InitGuideState(TypedDict):
    user_id: NotRequired[str]
    user_input: NotRequired[str]
    exp_id: NotRequired[str | None]
    messages: NotRequired[list[AnyMessage]]


def init(state: InitGuideState | GuideState) -> GuideState:
    logger.info("guide_graph: init")
    return {
        "user_id": state.get("user_id", ""),
        "user_input": state.get("user_input", ""),
        "exp_id": state.get("exp_id", None),
        "messages": state.get("messages", []),
    }


async def guide_reply(state: GuideState):
    logger.info("guide_graph: guide_reply")
    response = await guide_agent.ainvoke({"messages": state["messages"]})  # pyright: ignore[reportArgumentType]

    return {"messages": response.get("messages", [])}


def user_input(state: GuideState):
    user_input = interrupt("guide waiting for user input")
    logger.info("guide_graph: got user input")

    return {
        "messages": state["messages"] + [HumanMessage(user_input)],
        "user_input": user_input,
    }


guide_graph = (
    StateGraph(state_schema=GuideState, input_schema=InitGuideState)
    .add_node(init)
    .add_node(user_input)
    .add_node(guide_reply)
    .add_edge(START, "init")
    .add_edge("init", "user_input")
    .add_edge("guide_reply", "user_input")
    .add_edge("user_input", "guide_reply")
)


async def guide_init(user_id: int) -> str:
    logger.info(f"guide_graph: init for user {user_id}")
    guide_obj = await create_guide_session(user_id)
    guide_id = str(guide_obj.id)

    config: RunnableConfig = {"configurable": {"thread_id": guide_id}}
    if isinstance(compiled_graphs.guide_app.checkpointer, BaseCheckpointSaver):
        _ = await compiled_graphs.guide_app.checkpointer.adelete_thread(guide_id)

    init_state = InitGuideState()
    _ = await compiled_graphs.guide_app.ainvoke(init_state, config=config)

    return guide_id


async def guide_invoke(guide_id: str, model_prompt: str):
    logger.info(f"guide_graph: invoke for guide_id:{guide_id}")
    config: RunnableConfig = {"configurable": {"thread_id": guide_id}}

    response = await compiled_graphs.guide_app.ainvoke(
        Command(resume=model_prompt), config=config
    )
    last_ai_message: str = response["messages"][-1].content

    return "Ответ путеводителя:\n" + last_ai_message
