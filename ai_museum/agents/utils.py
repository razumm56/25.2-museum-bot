import numpy as np
from sqlalchemy import select

from ai_museum.db.create_tabels import Exhibit, Session
from ai_museum.agents.llm import LLMFactory

embedder = LLMFactory.get_embeddings("gigachat")

def get_embedding(text: str) -> list[float]:
    """Получение эмбеддинга для текста"""
    return embedder.embed_query(text)

def search_similar_exhibits(query: str, k: int = 3) -> list:
    """Поиск похожих экспонатов по запросу"""
    query_embedding = get_embedding(query)
    
    with Session() as session:
        # Поиск по косинусной близости
        stmt = (
            select(Exhibit)
            .order_by(Exhibit.embeddings.cosine_distance(query_embedding))
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

def get_exps_names_by_ids(exps_ids: list) -> list:
    with Session() as session:
        # Поиск по косинусной близости
        stmt = (
            select(Exhibit.name)
            .where(Exhibit.id.in_(exps_ids))
        )
        results = session.execute(stmt).scalars().all()
    return results