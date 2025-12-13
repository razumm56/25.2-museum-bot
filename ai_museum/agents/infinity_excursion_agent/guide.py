from typing import Literal, TypedDict

from langchain.agents import AgentState, create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.state import END, Command, RunnableConfig
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from loguru import logger

from ai_museum.agents.llm import LLMFactory
from ai_museum.agents.infinity_excursion_agent.expert import expert_app

llm = LLMFactory.get_llm("gigachat")

SYSTEM_PROMPT = """
Ты виртуальный экскурсовод в музее. Ты выступаешь в роли проводника к экспонатам.
"""
guide_agent = create_agent(llm, system_prompt=SYSTEM_PROMPT)


# ллм для определения следующего действия
ACTION_PICKER_PROMPT = SystemMessage("""
Ты помощник гида в музее
Ты получаешь сообщение пользователя и определяешь класс сообщения

continue - если пользователь просто общается
exit - если пользователь захотел уйти, или хоть как-то ищет выход
lead - если пользователь просит отвести его к экспонату с конкретным ID

НИКОГДА не отвечай пользователю, используй GuideAction ВСЕГДА
""")


class GuideAction(BaseModel):
    """Определяет дальнейшее действие гида: continue, lead или exit"""

    action: Literal["continue", "lead", "exit"] = Field(
        ..., description="Дальнейшее действие: continue|lead|exit"
    )
    exp_id: str | None = Field(None, description="ID экспоната, если action == 'lead'")


structured_llm = llm.with_structured_output(GuideAction, method="function_calling")


# граф
class GuideState(TypedDict):
    user_input: str
    exp_id: str | None
    agent_state: AgentState[None]


def init(state: GuideState):
    defaults = {
        "user_input": "",
        "exp_id": None,
        "agent_state": {"messages": []},
    }
    for key, value in defaults.items():
        state[key] = state.get(key, value)
    return state


def decide_next_move(state: GuideState):
    next_move = structured_llm.invoke(
        [ACTION_PICKER_PROMPT, HumanMessage(state["user_input"])]
    )
    if not isinstance(next_move, GuideAction):
        logger.info("модель не смогла вернуть правильный объект")
        return Command(goto="user_input")
    if not next_move:
        logger.info("модель не поняла класс сообщения")
        return Command(goto="user_input")
    if next_move.action == "lead" and not next_move.exp_id:
        logger.info("модель отправила к экспонату но не указала экспонат")
        return Command(goto="user_input")

    print(next_move.action)
    if next_move.action == "continue":
        return Command(goto="guide")
    elif next_move.action == "lead":
        return Command(update={"exp_id": next_move.exp_id}, goto="lead_to_exp")
    else:
        return Command(goto=END)


def guide(state: GuideState):
    logger.info("Ответ гида: ")
    agent_state: AgentState[None] = guide_agent.invoke(state["agent_state"])
    logger.info(agent_state["messages"][-1].content)

    return {"agent_state": agent_state}


def user_input(state: GuideState):
    user_input = interrupt("whaiting for user input")
    return {
        "agent_state": {
            "messages": state["agent_state"]["messages"] + [HumanMessage(user_input)]
        },
        "user_input": user_input,
    }


def lead_to_exp(state: GuideState, config: RunnableConfig):
    if not config.get("configurable", {}).get("thread_id", ""):
        raise RuntimeError("Couldn't find thread_id parameter")

    if not state["exp_id"]:
        raise RuntimeError("No exp_id to lead to")

    expert_thread_id: str = (
        config.get("configurable", {}).get("thread_id", "") + state["exp_id"]
    )

    config = {"configurable": {"thread_id": expert_thread_id}}
    expert_state = expert_app.invoke({"exp_id": state["exp_id"]}, config=config)

    return {
        "agent_state": {
            "messages": state["agent_state"]["messages"]
            + [AIMessage(f"Пользователь сходил к экспонату {state['exp_id']}")]
        }
    }


guide_graph = (
    StateGraph(state_schema=GuideState)
    .add_node(init)
    .add_node(user_input)
    .add_node(decide_next_move)
    .add_node(guide)
    .add_node(lead_to_exp)
    .add_edge(START, "init")
    .add_edge("init", "user_input")
    .add_edge("guide", "user_input")
    .add_edge("lead_to_exp", "user_input")
    .add_edge("user_input", "decide_next_move")
)

checkpointer = MemorySaver()
guide_app = guide_graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "1"}}

    state: GuideState = {}
    guide_state = guide_app.invoke(state, config=config)

    while "__interrupt__" in guide_state:
        user_input = input("Ввод:")
        guide_state = guide_app.invoke(Command(resume=user_input), config=config)
