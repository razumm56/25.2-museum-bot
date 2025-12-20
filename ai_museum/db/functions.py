from sqlalchemy.sql import select

from ai_museum.models.llm import LLMFactory
from .models import Exhibit, ExpertSession, GuideSession
from .init import AsyncSessionLocal, SessionLocal


def get_image_url(exhibit_id: int):
    with SessionLocal() as session:
        return session.execute(
            select(Exhibit.image_url).where(Exhibit.id == exhibit_id)
        ).scalar()


def get_description(exhibit_id: int):
    with SessionLocal() as session:
        return session.execute(
            select(Exhibit.description).where(Exhibit.id == exhibit_id)
        ).scalar()


async def create_guide_session(tg_user_id: int, id: str | None = None) -> GuideSession:
    async with AsyncSessionLocal() as session:
        guide_obj = GuideSession(id=id, tg_user_id=tg_user_id)
        session.add(guide_obj)
        await session.commit()
        await session.refresh(guide_obj)

    return guide_obj


async def create_expert_session(guide_id: str, exhibit_id: int):
    async with AsyncSessionLocal() as session:
        expert_obj = ExpertSession(guide_id=guide_id, exhibit_id=exhibit_id)
        session.add(expert_obj)
        await session.commit()
        await session.refresh(expert_obj)

    return expert_obj


async def get_user_chat_history(user_id: int) -> list[GuideSession]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GuideSession)
            .where(GuideSession.tg_user_id == user_id)
            .order_by(GuideSession.created_at.asc())
        )
        conversation_history = list(result.scalars().all())

    return conversation_history


async def get_user_exhibit_chat_history(
    guide_id: str, exhibit_id: int
) -> list[ExpertSession]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ExpertSession)
            .where(
                ExpertSession.exhibit_id == exhibit_id
                and ExpertSession.guide_id == guide_id
            )
            .order_by(ExpertSession.created_at.desc())
        )
        expert_conversation_history = list(result.scalars().all())

    return expert_conversation_history


embedder = LLMFactory.get_embeddings("gigachat")


def get_embedding(text: str) -> list[float]:
    """Получение эмбеддинга для текста"""
    return embedder.embed_query(text)


async def search_similar_exhibits(query: str, k: int = 3) -> list[Exhibit]:
    """Поиск похожих экспонатов по запросу"""
    query_embedding = get_embedding(query)

    async with AsyncSessionLocal() as session:
        # Поиск по косинусной близости
        stmt = await session.execute(
            select(Exhibit)
            .order_by(Exhibit.embedding.cosine_distance(query_embedding))
            .limit(k)
        )
        results = stmt.scalars().all()
        return list(results)
