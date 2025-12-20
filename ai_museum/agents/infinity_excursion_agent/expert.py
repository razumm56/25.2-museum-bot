from typing import NotRequired, Required, TypedDict

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import (
    END,
    START,
    Command,
    CompiledStateGraph,
    RunnableConfig,
)
from langgraph.types import interrupt
from loguru import logger

from ai_museum.models.llm import LLMFactory

llm = LLMFactory.get_llm("gigachat")


# агент эксперта
class AgentContext(TypedDict):
    exp_id: str


@dynamic_prompt
def agent_prompt(request: ModelRequest) -> str:
    exp_id = request.runtime.context.get("exp_id", "None")
    return f"Ты эксперт по конкретному экспонату в российском музее {exp_id}"


# TODO: этот тул не работает, нужно придумать тулом менять стейт тг бота
@tool
def end_excursion():
    """Завершает экскурсию"""
    return Command(goto=END), {"status": "ok"}


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


class InitExpertState(TypedDict):
    messages: NotRequired[list[AnyMessage]]
    exp_id: Required[int]


def init(state: InitExpertState):
    # logger.info("expert_graph: инит")
    defaults = {
        "messages": [],
        "exp_id": state["exp_id"],
    }
    for key, value in defaults.items():
        state[key] = state.get(key, value)
    return state


async def describe(state: ExpertState):
    # logger.info("expert_graph: генерация ответа эксперта")
    response = await agent.ainvoke(
        {"messages": state["messages"]},  # pyright: ignore[reportArgumentType]
        context={"exp_id": state["exp_id"]},
    )

    return {"messages": response.get("messages", [])}


def user_input(state: ExpertState):
    user_input = interrupt("waiting for user input")
    # logger.info("expert_graph: ввод юзера")
    return {
        "messages": state["messages"] + [HumanMessage(user_input)],
        "user_input": user_input,
    }


expert_graph = (
    StateGraph(state_schema=ExpertState, input_schema=InitExpertState)
    .add_node(init)
    .add_node(describe)
    .add_node(user_input)
    .add_edge(START, "init")
    .add_edge("init", "user_input")
    .add_edge("user_input", "describe")
    .add_edge("describe", "user_input")
)


#
def run_graph_chat(
    graph_app: CompiledStateGraph, thread: str, init_state, user_input: str
):
    config: RunnableConfig = {"configurable": {"thread_id": thread}}

    graph_snapshot = graph_app.get_state(config)
    if not graph_snapshot.next:  # initialize graph till interrupt
        _ = expert_app.invoke(init_state, config=config)

    guide_state = expert_app.invoke(Command(resume=user_input), config=config)

    return guide_state


if __name__ == "__main__":
    import asyncio

    subgraph_checkpointer = MemorySaver()
    expert_app = expert_graph.compile(subgraph_checkpointer)

    async def main(expert_app):
        config: RunnableConfig = {"configurable": {"thread_id": "1"}}

        state: InitExpertState = {"exp_id": 123}
        guide_state = expert_app.invoke(state, config=config)

        while "__interrupt__" in guide_state:
            resume_input = input("Ввод:")
            guide_state = await expert_app.ainvoke(
                Command(resume=resume_input), config=config
            )

    asyncio.run(main(expert_app))
