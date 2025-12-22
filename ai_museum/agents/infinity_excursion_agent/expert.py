from loguru import logger
import requests
from typing import NotRequired, Required, TypedDict

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import (
    END,
    START,
    Command,
    RunnableConfig,
)
from langgraph.types import interrupt

from ai_museum.agents.infinity_excursion_agent import compiled_graphs
from ai_museum.db.functions import (
    create_expert_session,
    get_description,
    get_exhibit_name,
)
from ai_museum.models.llm import LLMFactory
from .tools import web_search

llm = LLMFactory.get_llm("gigachat")


# агент эксперта
class AgentContext(TypedDict):
    exp_id: str
    exhibit_info: str


@dynamic_prompt
def agent_prompt(request: ModelRequest) -> str:
    exp_id = request.runtime.context.get("exp_id", "None")
    exhibit_info = request.runtime.context.get("exhibit_info", "")

    prompt = "Ты эксперт по конкретному экспонату в музее Словцова. Отвечай на вопросы пользователя, касающиеся ТОЛЬКО конкретного экспоната или текущего музея.\n"
    if exhibit_info:
        prompt += f"Информация об экспонате:\n{exhibit_info}\n"
    else:
        prompt += f"ID экспоната: {exp_id}\n"

    return prompt


agent = create_agent(
    llm,
    middleware=[agent_prompt],
    tools=[web_search],
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

    return {"messages": response.get("messages", [])}


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
    .add_edge("user_input", "describe")
    .add_edge("describe", "user_input")
)


async def expert_init(guide_id: str, exhibit_id: int) -> str:
    logger.debug(f"expert_graph: expert init for guide_id:{guide_id}")
    expert_obj = await create_expert_session(guide_id, exhibit_id)
    expert_id = str(expert_obj.id)

    config: RunnableConfig = {"configurable": {"thread_id": expert_id}}
    # удаляем thread_id если есть коллизия
    if isinstance(compiled_graphs.expert_app.checkpointer, BaseCheckpointSaver):
        _ = await compiled_graphs.expert_app.checkpointer.adelete_thread(expert_id)

    # получаем информацию об экспонате
    exhibit_name = get_exhibit_name(exhibit_id)
    exhibit_description = get_description(exhibit_id)
    exhibit_info = (
        f"Название {exhibit_name}, Описание: {exhibit_description}"
        if exhibit_description
        else ""
    )

    init_state = InitExpertState({"exp_id": exhibit_id, "exhibit_info": exhibit_info})
    _ = await compiled_graphs.expert_app.ainvoke(init_state, config=config)

    return expert_id


async def expert_invoke(expert_id: str, prompt: str):
    logger.debug(f"expert_graph: expert_invoke for expert_id:{expert_id}")
    config: RunnableConfig = {"configurable": {"thread_id": expert_id}}

    logger.debug(f"expert_graph expertid:{expert_id} invoke with '{prompt}'")

    response = await compiled_graphs.expert_app.ainvoke(
        Command(resume=prompt), config=config
    )
    last_ai_message: str = response["messages"][-1].content

    return "Ответ эксперта:\n" + last_ai_message
