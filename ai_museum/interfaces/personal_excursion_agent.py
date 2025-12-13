import asyncio

from uuid import uuid4
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import Command
from loguru import logger

from ai_museum.agents.personal_excursion_agent.agent import PersonalGuideState, guide_app, guide_graph
from ai_museum.db.create_tabels import get_description


class PersonalExcursionAgent:
    def __init__(self, user_description: str):
        self.config = {"configurable": {"thread_id": uuid4()}}
        self.state: PersonalGuideState = {}
        self.guide_state = None
        self.user_description = user_description
        # self.state: PersonalGuideState = {"user_description": self.user_description}

    async def start_excursion(self, user_id: str=""):
        self.guide_state = guide_app.invoke(self.state, config=self.config)
        
        return True

    
    async def choose_excursion_len(self, excursion_len: int):
        if self.guide_state:
            self.guide_state = guide_app.invoke(Command(resume=excursion_len), config=self.config) 
        else:
            logger.error("Ошибка: граф еще не создан")
            raise Exception
        
    async def send_greeting(self):
        return self.guide_state["agent_state"]['content']
        

    async def generate_answer(self, question=str):
        self.guide_state = guide_app.invoke(Command(resume=question), config=self.config)
        logger.info(f"Состояние графа: {self.guide_state}")
        print('!!!!!!', self.guide_state["agent_state"])
        return self.guide_state["agent_state"]['content']
   
    async def generate_description(self):
        self.guide_state = guide_app.invoke(Command(resume="next"), config=self.config) 
        return self.guide_state["agent_state"]['content']
   
