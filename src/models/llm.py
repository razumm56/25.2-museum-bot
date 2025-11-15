import asyncio

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import Command
from agent.guide import guide_app, guide_graph, GuideState
from loguru import logger
from db.create_tabels import get_description


class LLM:
    def __init__(self):
        self.config = {"configurable": {"thread_id": "1"}}
        self.state: GuideState = {}

    async def generate_description(self, exhibit_id: int):
        return get_description(exhibit_id)
        guide_state = guide_app.invoke(self.state, config=self.config)
        guide_state = guide_app.invoke(Command(resume="начало экскурсии"), config=self.config)
        return guide_state["agent_state"]["messages"][-1].content

    async def generate_answer(self, question: str):
        return 'Вместо ответа'
        checkpointer = MemorySaver()
        guide_app = guide_graph.compile(checkpointer=checkpointer)
        
        guide_state = guide_app.invoke(self.state, config=self.config)
        guide_state = guide_app.invoke(Command(resume=question), config=self.config)
        logger.info(guide_state)
        return guide_state["agent_state"]["messages"][-1].content