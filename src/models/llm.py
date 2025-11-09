import asyncio

class LLM:

    async def generate_description(self, exhibit_id: int):
        await asyncio.sleep(1)
        return f'Описание экспоната №{exhibit_id}.\nОчень крутой экспонат!'

    async def generate_answer(self, question: str):
        await asyncio.sleep(1)
        return f'Отличный вопрос! Правда я без понятия как на него ответить'