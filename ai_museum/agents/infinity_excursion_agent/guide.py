from typing import NotRequired, TypedDict

from langchain.agents import AgentState, create_agent
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
)
from langgraph.graph import START, StateGraph
from langgraph.types import interrupt
from loguru import logger

from ai_museum.models.llm import LLMFactory

from .tools import web_search, clean_message

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
Ты виртуальный экскурсовод в музее И. Я. Словцова. Ты выступаешь в роли проводника к экспонатам.
ВАЖНО! НЕ ВЫЗЫВАЙ web_search НЕСКОЛЬКО РАЗ
"""
guide_agent = create_agent(
    llm,
    tools=[web_search],
    system_prompt=SYSTEM_PROMPT,
    state_schema=AgentState,
    context_schema=EmptyContext,
    debug=True,
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
    logger.debug("guide_graph: init")
    return {
        "user_id": state.get("user_id", ""),
        "user_input": state.get("user_input", ""),
        "exp_id": state.get("exp_id", None),
        "messages": state.get("messages", []),
    }


async def guide_reply(state: GuideState):
    logger.debug("guide_graph: guide_reply")
    response = await guide_agent.ainvoke({"messages": state["messages"]})  # pyright: ignore[reportArgumentType]

    messages = response.get("messages")
    if messages:
        messages[-1] = clean_message(messages[-1])

    return {"messages": messages}


def user_input(state: GuideState):
    user_input = interrupt("guide waiting for user input")
    logger.debug("guide_graph: got user input")

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
