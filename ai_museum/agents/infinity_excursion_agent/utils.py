import numpy as np
from sqlalchemy import select

from ai_museum.db.create_tabels import Exhibit, Session
from ai_museum.agents.llm import LLMFactory

embedder = LLMFactory.get_embeddings("gigachat")

def get_embedding(text: str) -> list[float]:
    """Получение эмбеддинга для текста"""
    return embedder.embed_query(text)

def search_similar_exhibits(query: str, k: int = 3) -> list[Exhibit]:
    """Поиск похожих экспонатов по запросу"""
    query_embedding = get_embedding(query)
    
    with Session() as session:
        # Поиск по косинусной близости
        stmt = (
            select(Exhibit)
            .order_by(Exhibit.embedding.cosine_distance(query_embedding))
            .limit(k)
        )
        results = session.execute(stmt).scalars().all()
        return results

def format_exhibit_context(exhibits: list[Exhibit]) -> str:
    """Форматирование информации об экспонатах в контекст"""
    context = "\n\nДоступные экспонаты:\n"
    for exhibit in exhibits:
        context += f"- ID: {exhibit.id}, Название: {exhibit.name}, Описание: {exhibit.description}\n"
    return context

#TODO убрать
# dialog = "dasdsadasdasdasdsadasdasdasdasdasd"

# exps = search_similar_exhibits(dialog) # 3 ближайших по тексту
# contex = format_exhibit_context(exps) # 3 ближайших по тексту в виде текст
# prompt = f"Выбери 1 экспонат, который наиболее пойдет пользователю, экспонаты {contex}, предыдущий диалог {dialog[:2000]}" # -> 1-3 1 
# format_exhibit_context(exps[0]) # Информация по наиболее релевантному экспонату