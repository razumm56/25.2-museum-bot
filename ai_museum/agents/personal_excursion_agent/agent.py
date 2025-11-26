import sys

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
from ai_museum.agents.prompts import ACTION_PICKER_PROMPT, GREETING_PROMPT, ANSWER_USER_QUESTION, DESCRIBE_EXP_PROMT
from ai_museum.agents.personal_excursion_agent.expert import expert_app
from ai_museum.agents.utils import search_similar_exhibits, get_exps_names_by_ids

#TODO удалить настройку логера
logger.remove()  # Удаляет стандартный обработчик  
logger.add(sys.stderr, level="DEBUG") 

llm = LLMFactory.get_llm("gigachat")

SYSTEM_PROMPT = """
Ты виртуальный экскурсовод в музее. Ты выступаешь в роли проводника к экспонатам.
"""
guide_agent = create_agent(llm, system_prompt=SYSTEM_PROMPT)

class PersonalGuideAction(BaseModel):
    """Определяет дальнейшее действие гида: continue, lead или exit"""

    action: Literal["continue", "lead", "exit"] = Field(
        ..., description="Дальнейшее действие: continue|lead|exit"
    )
    exp_id: str | None = Field(None, description="ID экспоната, если action == 'lead'")


structured_llm = llm.with_structured_output(PersonalGuideAction, method="function_calling")


# граф
class PersonalGuideState(TypedDict):
    user_input: str
    exp_id: str
    exps_ids_description: dict
    agent_state: AgentState[None]
    excursion_len: int
    current_exp_num: int
    user_description: str

def init(state: PersonalGuideState):
    defaults = {
        "user_input": "",
        "exps_ids_description": {},
        "agent_state": {"messages": []},
        "current_exp_num": -1,
        "user_description": ""
    }
    for key, value in defaults.items():
        state[key] = state.get(key, value)
    return state
 
def choose_excursion_len(state: PersonalGuideState):
    if state.get('excursion_len'):
        return {"excursion_len": state['excursion_len']}
    
    excursion_len = interrupt("waiting for user choose excursion len")
    
    return {"excursion_len": excursion_len}
    

def decide_next_move(state: PersonalGuideState):
    logger.info(f"Запрос пользователя: {state["user_input"]}")

    if state["user_input"] == "next":
        state['current_exp_num'] += 1
        if state["current_exp_num"] >= state["excursion_len"]:
            return Command(goto=END)
        return Command(goto="guide")
    else:
        exp_id = list(state["exps_ids_description"].keys())[state["current_exp_num"]]
        return Command(update={"exp_id": exp_id}, goto="lead_to_exp")


def guide(state: PersonalGuideState):
    logger.info("Ответ гида: ")

    state["exp_id"] = list(state["exps_ids_description"].keys())[state["current_exp_num"]]
    exp_description = state['exps_ids_description'][state['exp_id']]
    answer = llm.invoke(DESCRIBE_EXP_PROMT(exp_description=exp_description))
    logger.info(answer)
    state['agent_state'] = answer
    return state

def user_input(state: PersonalGuideState):
    user_input = interrupt("waiting for user input")
    logger.info(f"Запрос пользователя: {user_input}")
    if user_input:
        return {
            "user_input": user_input,
        }
    else:
        return {"user_input": ""}
    
def choose_exps_ids(state: PersonalGuideState):
    logger.info(f"Описание пользователя: {state['user_description']}")
    logger.info(f"Количество экспонатов: {state['excursion_len']}")
    personal_exps = search_similar_exhibits(query=state['user_description'], k=state['excursion_len'])
    for exp in personal_exps:
        state['exps_ids_description'].update({getattr(exp, 'id'): [getattr(exp, 'description'), getattr(exp, 'name')]})
    logger.info(f"Экспонаты: {state['exps_ids_description']}")
    
    return state
    
def generate_greeting(state: PersonalGuideState):
    exp_names = [exp[1] for exp in state["exps_ids_description"].values()]
    logger.info(f"Названия экспонатов: {exp_names}")
    greeting = llm.invoke(GREETING_PROMPT(exps_names=str(exp_names)))
    logger.info(f"Приветствие гида: {greeting}")
    state["agent_state"] = greeting
    
    return state

def lead_to_exp(state: PersonalGuideState, config: RunnableConfig):
    if not config.get("configurable", {}).get("thread_id", ""):
        raise RuntimeError("Couldn't find thread_id parameter")

    if not state["exp_id"]:
        raise RuntimeError("No exp_id to lead to")

    expert_thread_id: str = (
        config.get("configurable", {}).get("thread_id", "")
    )
    
    config = {"configurable": {"thread_id": expert_thread_id}}
    expert_state = expert_app.invoke({"exp_description": state['exps_ids_description'][state["exp_id"]], "user_input": state["user_input"]}, config=config)

    return {
        "agent_state": expert_state
    }


guide_graph = (
    StateGraph(state_schema=PersonalGuideState)
    .add_node(init)
    .add_node(choose_excursion_len)
    .add_node(choose_exps_ids)
    .add_node(generate_greeting)
    .add_node(user_input)
    .add_node(decide_next_move)
    .add_node(guide)
    .add_node(lead_to_exp)
    .add_edge(START, "init")
    .add_edge("init", "choose_excursion_len")
    .add_edge("choose_excursion_len", "choose_exps_ids")
    .add_edge("choose_exps_ids", "generate_greeting")
    .add_edge("generate_greeting", "user_input")
    .add_edge("guide", "user_input")
    .add_edge("lead_to_exp", "user_input")
    .add_edge("user_input", "decide_next_move")
)

checkpointer = MemorySaver()
guide_app = guide_graph.compile(checkpointer=checkpointer)
