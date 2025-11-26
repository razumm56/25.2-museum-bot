from typing import TypedDict

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import END, START
from loguru import logger

from ai_museum.agents.llm import LLMFactory
from ai_museum.agents.prompts import DESCRIBE_EXP_PROMT, ANSWER_USER_QUESTION
llm = LLMFactory.get_llm("gigachat")


# агент эксперта

agent = create_agent(
    llm,
)


# граф эксперта
class ExpertState(TypedDict):
    agent_state: str
    exp_description: str
    user_input: str

def init(state: ExpertState):
    defaults = {
        "agent_state": "", 
        "exp_description": state["exp_description"],
    }
    for key, value in defaults.items():
        state[key] = state.get(key, value)
    return state


def describe(state: ExpertState):
    logger.info("Ответ эксперта:")
    agent_state = llm.invoke(
        ANSWER_USER_QUESTION(state["user_input"], state["exp_description"])
    )
        
    logger.info(agent_state)

    return {"agent_state": agent_state}


expert_graph = (
    StateGraph(state_schema=ExpertState)
    .add_node(init)
    .add_node(describe)
    .add_edge(START, "init")
    .add_edge("init", "describe")
    .add_edge("describe", END)
)


subgraph_checkpointer = MemorySaver()
expert_app = expert_graph.compile(subgraph_checkpointer)
