import uuid
from datetime import datetime, timezone
from typing import final

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    UUID,
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


@final
class Exhibit(Base):
    __tablename__ = "exhibits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    text: Mapped[str] = mapped_column(String())
    short_description: Mapped[str] = mapped_column(String())
    nodes: Mapped[JSON] = mapped_column(JSON(), nullable=True)
    image_url: Mapped[str] = mapped_column(String(), nullable=True)
    embeddings: Mapped[Vector] = mapped_column(Vector(1024))
    image: Mapped[str] = mapped_column(String(), nullable=True)


@final
class GuideSession(Base):
    __tablename__ = "langgraph_guide"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )


@final
class ExpertSession(Base):
    __tablename__ = "langgraph_expert"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    guide_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(GuideSession.id), nullable=False
    )
    exhibit_id: Mapped[int] = mapped_column(ForeignKey(Exhibit.id), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )
