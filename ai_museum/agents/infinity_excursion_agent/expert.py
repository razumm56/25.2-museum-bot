from typing import NotRequired, Required, TypedDict

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph import StateGraph
from langgraph.graph.state import (
    START,
)
from langgraph.types import interrupt
from loguru import logger

from ai_museum.models.llm import LLMFactory

from .tools import clean_message, web_search

llm = LLMFactory.get_llm("gigachat")


# агент эксперта
class AgentContext(TypedDict):
    exp_id: str
    exhibit_info: str


@dynamic_prompt
def agent_prompt(request: ModelRequest) -> str:
    exp_id = request.runtime.context.get("exp_id", "None")
    exhibit_info = request.runtime.context.get("exhibit_info", "")

    prompt = (
        "Ты эксперт по конкретному экспонату в музее И. Я. Словцова. Отвечай на вопросы пользователя, касающиеся ТОЛЬКО конкретного экспоната или текущего музея.\n"
        "ВАЖНО! НЕ ВЫЗЫВАЙ web_search НЕСКОЛЬКО РАЗ \n"
    )
    if exhibit_info:
        prompt += f"Информация об экспонате:\n{exhibit_info}\n"
    else:
        prompt += f"ID экспоната: {exp_id}\n"

    return prompt


agent = create_agent(
    llm,
    middleware=[agent_prompt],
    context_schema=AgentContext,
    state_schema=AgentState,
)


# граф эксперта
class ExpertState(TypedDict):
    messages: list[AnyMessage]
    exp_id: int
    exhibit_info: str


class InitExpertState(TypedDict):
    messages: NotRequired[list[AnyMessage]]
    exp_id: Required[int]
    exhibit_info: Required[str]


def init(state: InitExpertState):
    logger.debug("expert_graph: init")
    defaults = {
        "messages": [],
        "exp_id": state["exp_id"],
        "exhibit_info": state.get("exhibit_info", ""),
    }
    for key, value in defaults.items():
        state[key] = state.get(key, value)
    return state


async def expert_reply(state: ExpertState):
    logger.debug("expert_graph: expert_reply")
    response = await agent.ainvoke(
        {"messages": state["messages"]},  # pyright: ignore[reportArgumentType]
        context={
            "exp_id": str(state["exp_id"]),
            "exhibit_info": state.get("exhibit_info", ""),
        },
    )

    messages = response.get("messages")
    if messages:
        messages[-1] = clean_message(messages[-1])

    return {"messages": messages}


def user_input(state: ExpertState):
    user_input = interrupt("waiting for user input")
    logger.debug("expert_graph: got user input")

    return {
        "messages": state["messages"] + [HumanMessage(user_input)],
        "user_input": user_input,
    }


expert_graph = (
    StateGraph(state_schema=ExpertState, input_schema=InitExpertState)
    .add_node(init)
    .add_node(expert_reply)
    .add_node(user_input)
    .add_edge(START, "init")
    .add_edge("init", "user_input")
    .add_edge("user_input", "expert_reply")
    .add_edge("expert_reply", "user_input")
)
