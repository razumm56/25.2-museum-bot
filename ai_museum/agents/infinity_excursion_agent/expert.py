from typing import TypedDict

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import END, START

from ai_museum.agents.llm import LLMFactory

llm = LLMFactory.get_llm("gigachat")


# агент эксперта
class AgentContext(TypedDict):
    exp_id: str


@dynamic_prompt
def agent_prompt(request: ModelRequest) -> str:
    exp_id = request.runtime.context.get("exp_id", "None")
    return f"Ты эксперт по конкретному экспонату в российском музее {exp_id}"


agent = create_agent(
    llm,
    middleware=[agent_prompt],
    context_schema=AgentContext,
)


# граф эксперта
class ExpertState(TypedDict):
    agent_state: AgentState[None]
    exp_id: str


def init(state: ExpertState):
    defaults = {
        "agent_state": {
            "messages": [HumanMessage("Привет")],
            "exp_id": state["exp_id"],
        },
    }
    for key, value in defaults.items():
        state[key] = state.get(key, value)
    return state


def describe(state: ExpertState):
    print("Ответ эксперта:")
    agent_state: AgentState[None] = agent.invoke(
        state["agent_state"], context={"exp_id": state["exp_id"]}
    )
    print(agent_state["messages"][-1].content)

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
